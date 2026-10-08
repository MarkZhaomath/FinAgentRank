"""FinAgentRank · 真实点星校验后端（步骤5 · 纯标准库，无依赖）。

把前端"Star to submit"做成真实校验：
  1) GET /auth/github  → 302 跳转 GitHub OAuth 授权
  2) GitHub 回跳 /auth/callback?code=... → 换 access_token → 取 login
  3) GET /user/starred/{owner}/{repo} → 204=已点星(verified) / 404=未点星
  4) 前端轮询 /api/star-check?login=... → {verified, login, owner, repo}

运行（需先建 GitHub OAuth App 填环境变量）：
    GITHUB_CLIENT_ID=xxx GITHUB_CLIENT_SECRET=yyy \
    GITHUB_REPO=yourorg/FinAgentRank BASE_URL=http://localhost:8001 \
    python src/finagentrank/star_server.py

生产注意：内存态仅作演示；正式用有状态存储（DB/Redis）承载 verified 会话。
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

# 直跑时把 src 加进路径，保证可 import finagentrank.conformance
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 复用 conformance 校验（manifest 校验 + 在线握手）
from finagentrank.conformance import conformance_check

CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "YOUR_CLIENT_ID")
CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "YOUR_CLIENT_SECRET")
REPO = os.environ.get("GITHUB_REPO", "yourorg/FinAgentRank")  # owner/name
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8001")

# 演示用内存会话：login -> 是否已点星（正式用持久化）
verified_sessions: dict[str, bool] = {}


def _get(url: str, headers: dict) -> tuple[int, str]:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:
        return -1, ""


def _post(url: str, data: dict) -> str:
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(),
                                 headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read().decode()
    except Exception as e:
        return json.dumps({"error": type(e).__name__})


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: str, ct: str = "application/json"):
        self.send_response(status)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body.encode())

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)

        # 1) 发起 OAuth
        if u.path == "/auth/github":
            params = urllib.parse.urlencode({
                "client_id": CLIENT_ID, "scope": "public_repo",
                "redirect_uri": f"{BASE_URL}/auth/callback",
            })
            self.send_response(302)
            self.send_header("Location", f"https://github.com/login/oauth/authorize?{params}")
            self.end_headers()
            return

        # 2) OAuth 回跳：换 token → 取 login → 查星标 → 记 verified
        if u.path == "/auth/callback":
            q = urllib.parse.parse_qs(u.query)
            code = (q.get("code") or [""])[0]
            if not code:
                return self._send(400, json.dumps({"error": "no_code"}))
            # 换 token
            tok_json = _post("https://github.com/login/oauth/access_token", {
                "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "code": code,
            })
            token = json.loads(tok_json).get("access_token")
            if not token:
                return self._send(502, json.dumps({"error": "token_exchange_failed"}))
            # 取 login
            _, user = _get("https://api.github.com/user",
                           {"Authorization": f"Bearer {token}", "Accept": "application/json"})
            try:
                login = json.loads(user).get("login")
            except Exception:
                return self._send(502, json.dumps({"error": "user_fetch_failed"}))
            # 查星标：204 = 已点星，404 = 未点
            star, _ = _get(f"https://api.github.com/user/starred/{REPO}",
                           {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
            verified = star == 204
            verified_sessions[login] = verified
            return self._send(200, json.dumps({"verified": verified, "login": login,
                                               "repo": REPO, "star_status": star}))

        # 3) 前端轮询：该账号是否已点星
        if u.path == "/api/star-check":
            q = urllib.parse.parse_qs(u.query)
            login = (q.get("login") or [""])[0]
            verified = verified_sessions.get(login, False)
            return self._send(200, json.dumps({"verified": verified, "login": login}))

        # 4) 健康检查
        if u.path == "/health":
            return self._send(200, json.dumps({"ok": True, "repo": REPO}))
        self._send(404, json.dumps({"error": "not_found"}))

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        # 提交前 conformance 校验：收 manifest → manifest 校验 + 在线握手 → 返回通过/失败+修复建议
        if u.path == "/api/conformance":
            try:
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b"{}"
                manifest = json.loads(body.decode() or "{}")
            except Exception:
                return self._send(400, json.dumps({"error": "bad_json"}))
            try:
                # 真握手：urllib 实发 {endpoint}/health（短超时，诚实报超时/不可达）
                result = conformance_check(manifest, timeout_s=4.0)
            except Exception as e:
                return self._send(500, json.dumps({"error": type(e).__name__}))
            return self._send(200, json.dumps(result))
        return self._send(404, json.dumps({"error": "not_found"}))

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    print(f"FinAgentRank star-check server on http://localhost:{port}")
    print(f"  repo={REPO} · base={BASE_URL} · client_id={'set' if CLIENT_ID != 'YOUR_CLIENT_ID' else 'UNSET'}")
    HTTPServer(("", port), Handler).serve_forever()
