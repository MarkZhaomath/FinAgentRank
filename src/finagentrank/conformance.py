"""FinAgentRank · 接入标准 / Conformance 校验（步骤4 · 引擎5落地）。

对应调研引擎5 + 白皮书 §5「接入标准」。不发明私有格式——入驻 = 通过统一 manifest +
在线握手扫描（学 Glama 的 initialize+tools/list 实发握手 + 修复建议）。

- validate_manifest：manifest 字段校验（必填项 / 能力族合法 / 输出类型枚举 / 出口清单）。
- handshake：在线握手（默认 urllib 实发，可注入 transport 便于测试）→ 状态 + 延迟 + 声明能力。
- 信任判定：握手通过 且 manifest 校验无致命错误 → conformance=pass；否则给修复建议。
纯标准库。
"""

from __future__ import annotations

import json
import time
import urllib.request
from typing import Callable

# 合法能力族（与 TAXONOMY 对齐；正式版 4 层 14 类）
VALID_FAMILIES = ["Data", "Factor", "Research", "Risk", "Signal", "Backtest"]

# 合法输出类型（金融口径枚举，防乱声明）
VALID_OUTPUT_TYPES = {"research", "signal", "data", "risk", "backtest", "factor"}

# manifest 必填字段
REQUIRED_FIELDS = ["name", "name_for_model", "endpoint", "auth", "capabilities",
                   "output_type", "egress_hosts", "schema_version"]

Transport = Callable[[str, dict], tuple[int, dict]]  # (method,payload)->(status,json)


def validate_manifest(m: dict) -> list[str]:
    """manifest 字段校验。返回错误列表（空 = 通过）。致命错误 vs 建议分开。"""
    errors: list[str] = []
    for f in REQUIRED_FIELDS:
        if f not in m or m[f] in (None, ""):
            errors.append(f"missing_required:{f}")
    if "endpoint" in m and m["endpoint"]:
        if not (m["endpoint"].startswith("https://") or m["endpoint"].startswith("http://")):
            errors.append("bad_endpoint_url")
    caps = m.get("capabilities") or []
    bad = [c for c in caps if c not in VALID_FAMILIES]
    if bad:
        errors.append(f"invalid_capability:{bad}")
    if not caps:
        errors.append("empty_capabilities")
    if m.get("output_type") and m["output_type"] not in VALID_OUTPUT_TYPES:
        errors.append(f"invalid_output_type:{m['output_type']}")
    egress = m.get("egress_hosts") or []
    if not isinstance(egress, list) or not egress:
        errors.append("missing_egress_hosts")
    return errors


def handshake(endpoint: str, transport: Transport | None = None,
              timeout_s: float = 5.0) -> dict:
    """在线握手：GET {endpoint}/health（或注入 transport 模拟）。

    返回 {ok, latency_ms, status, declared, note}。
    - ok：返回 200 且体为 JSON。
    - declared：握手体里声明的 capabilities（供对照）。
    """
    if transport is not None:
        t0 = time.time()
        status, body = transport(endpoint + "/health", {})
        latency = (time.time() - t0) * 1000
    else:
        t0 = time.time()
        try:
            with urllib.request.urlopen(endpoint + "/health", timeout=timeout_s) as r:
                status = r.status
                body = json.loads(r.read().decode() or "{}")
        except Exception as e:  # 网络/超时/非 JSON
            return {"ok": False, "latency_ms": None, "status": None,
                    "declared": {}, "note": f"handshake_failed:{type(e).__name__}"}
        latency = (time.time() - t0) * 1000
    ok = status == 200 and isinstance(body, dict)
    return {"ok": ok, "latency_ms": round(latency, 1), "status": status,
            "declared": body.get("capabilities", []),
            "note": "" if ok else f"unexpected:{status}"}


def conformance_check(manifest: dict, transport: Transport | None = None,
                      timeout_s: float = 5.0) -> dict:
    """整体准入判定：manifest 校验 + 在线握手。

    返回 {passed, errors, handshake, suggestions}。passed=无致命错误且握手通过。
    """
    errs = validate_manifest(manifest)
    hs = handshake(manifest.get("endpoint", ""), transport, timeout_s=timeout_s)
    passed = (not errs) and hs["ok"]
    suggestions: list[str] = []
    if errs:
        suggestions.append("fix_manifest:" + ",".join(errs[:5]))
    if not hs["ok"]:
        suggestions.append(hs["note"] or "handshake_failed")
    return {"passed": passed, "errors": errs, "handshake": hs,
            "suggestions": suggestions[:4]}


def check_declared_vs_measured(declared: list[str], measured_top: str | None) -> str | None:
    """声明 vs 实测自动分类对照（§9.1）：声明≠实测最强族 → 提示（以实测为准）。"""
    if measured_top and declared and measured_top not in declared:
        return f"declared {declared} but measured top={measured_top} — measured wins"
    return None
