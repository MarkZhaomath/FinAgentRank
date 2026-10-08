# FinAgentRank · Web（静态榜站 · 工作版 v0）

> 一期开源的**前端界面**：纯静态 HTML + ECharts，零构建、零依赖，clone 下来一句命令跑出漂亮榜站。
> 目标客户群：全世界（界面英文、社媒分享全球向）。

## 运行（任选其一）

    cd FinAgentRank-web
    python3 -m http.server 8000
    # 浏览器打开 http://localhost:8000

或直接双击 `index.html`（数据已内嵌，无需 fetch）。

## 已实现（真实数据 · 引擎直连）

1. **榜单主页（真实分）**：`leaderboard.json`（C1–C4 评测引擎输出）→ 能力分 ± 95% CI + Top % 分位 + 能力族强度条 + 自动分类（top_family）+ official 状态。不再用 mock。
2. **对比**：ECharts 雷达，选 2 个 Agent 对比 6 能力族画像（真实 per_family）。
3. **提交流程（强制点星·真实校验）**：Star to submit → 后端 `/auth/github` GitHub OAuth → `/user/starred/{repo}` 真校验 → 前端轮询 `/api/star-check` 解锁（后端 `FinAgentRank/src/finagentrank/star_server.py`，默认 `http://localhost:8001`）。
4. **一键社媒分享（全球向）**：X / LinkedIn / Reddit / Hacker News / Bluesky / Facebook / Telegram / WhatsApp / 复制链接 + Open Graph 卡片；分享文案动态取当前第 1 名。

## 数据来源

- `leaderboard.json` = `FinAgentRank` 评测引擎（C1–C4 + walk-forward + 自动分类）的真实输出，同目录随引擎重跑更新。
- 前端 fetch `leaderboard.json`；若 file:// 打开 fetch 失败，自动用内嵌兜底（同一份真实数据）。

## 技术要点

- `echarts.min.js` 已本地 vendor（1MB），clone 后离线可跑。
- 榜单数据来自真实评测引擎 JSON；引擎重跑后替换 `leaderboard.json` 即可刷新榜单。
- 同份静态前端可原样打包为 Hugging Face Space 上线（带提交通道）。

## 结构

    FinAgentRank-web/
      index.html          # 榜站单页（榜单 + 对比 + 提交 + 分享）
      leaderboard.json    # 评测引擎真实输出（fetch 数据源）
      echarts.min.js      # 本地 ECharts（离线）
      README.md

## 将来 GitHub 建仓后一键推送

    git add -A && git commit -m "批次-FinAgentRank-web 榜单接入引擎真实分" && git push --set-upstream origin dev
