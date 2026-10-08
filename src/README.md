# FinAgentRank · 评测引擎核心（C1–C4 能力分 · 工作版 v0）

> 一期关键路径第一项：客观评测引擎最小可用。产出**真实能力分**，前端 FinAgentRank-web 用它的 JSON 替换 mock。

## 运行

    cd FinAgentRank
    python src/finagentrank/run_demo.py    # C1–C4 能力分 + 自动分类
    python src/finagentrank/run_step2.py   # 切分 + 哈希 + 防作弊四件套
    python src/finagentrank/run_step3.py   # SCORING 正式化（n_min + 入榜门槛）
    python src/finagentrank/run_step4.py   # 接入标准 / conformance 校验
    python src/finagentrank/run_step5.py   # （点星后端：见下方"点星校验后端"）

## 已实现

- **C1–C4 四类客观评测**：C1 客观复算(口径/精确) · C2 因子复算(信号/相关) · C3 稳健性(跨 seed/regime 低方差) · C4 决策支持。
- **能力分**：按 TAXONOMY 能力族合成（6 族简化示意），C1–C4 加权；每族给分 + **bootstrap 95% CI**。
- **SCORING 正式化**（`scoring.py`）：C1–C4 判分/权重/容差/n_min/入榜门槛（capability≥0.5 且 CI半宽≤0.25）单一事实来源；观测不足(<n_min) 标 insufficient 不给分。
- **walk-forward**：强制时序切分（前 70 训练 / 后 30 样本外），防前视。
- **自动分类**：跑完评测后按"各能力族实测最强"自动归类（`top_family`）——不是开发者自报（§9.1 最强功能）。
- **数据集治理**（`dataset.py`）：测试题切分成**公开开发集 + 封闭保密测试集**；保密集**可哈希**（HMAC-SHA256 指纹，防篡改/抄底/证明真值）；MinHash n-gram 指纹近重复/抄底检测。
- **防作弊四件套**（`anticheat.py`）：① 提交限流+门槛 ② 草稿→正式两级 ③ 身份聚类合并小号 ④ 时间隔离+季度轮换 seed。
- **接入标准 / conformance**（`conformance.py`）：manifest 字段校验（必填/能力族/输出类型枚举/出口）+ 在线握手扫描；声明 vs 实测自动分类对照（§9.1，以实测为准）。
- **点星校验后端**（`star_server.py`）：GitHub OAuth → `/user/starred/{repo}` 真校验 → 前端轮询解锁。纯标准库。
- **排行榜 JSON**：`src/finagentrank/leaderboard.json`，前端 FinAgentRank-web 直连（同构替换 mock）。

## 演示验证

- 容差复算：误差 0.02→1.0，误差 0.15→衰减归 0；因子相关近线性→≈1.0。
- 排名：好 Agent > 漂移 > 坏；自动分类命中各 Agent 专精族（Factor/Risk/Signal）。
- 步骤2：切分无重叠、保密集指纹防篡改、抄底近重复命中、四件套全部通过。
- 步骤3：n_min 不足标 insufficient、入榜门槛判定生效、无回归。
- 步骤4：合规 manifest 通过；缺陷 manifest + 握手超时拦截并给修复建议；声明vs实测对照正确。
- 步骤5：后端 /health、OAuth 302、star-check 轮询、前端 JS 语法、端到端冒烟全部通过。

## 点星校验后端（步骤5）

    GITHUB_CLIENT_ID=xxx GITHUB_CLIENT_SECRET=yyy \
    GITHUB_REPO=yourorg/FinAgentRank BASE_URL=http://localhost:8001 \
    python src/finagentrank/star_server.py

需要先在 GitHub 建 OAuth App（回调地址 `{BASE_URL}/auth/callback`）。前端 `FinAgentRank-web` 的 "Star to submit" 已接 `http://localhost:8001`。内存会话仅演示，正式用持久化存储。

## 结构

    FinAgentRank/
      src/finagentrank/
        score.py          # 评测引擎核心（C1-C4 + CI + walk-forward + 自动分类）
        scoring.py        # SCORING 正式规则（单一事实来源）
        dataset.py        # 开发集/保密集切分 + 哈希 + 指纹近重复检测
        anticheat.py      # 防作弊四件套（限流/两级/身份聚类/时间隔离）
        conformance.py    # 接入标准 / manifest 校验 + 握手
        star_server.py    # 点星校验后端（GitHub OAuth）
        run_demo.py       # C1–C4 端到端跑
        run_step2.py      # 切分+哈希+四件套
        run_step3.py      # SCORING 正式化
        run_step4.py      # conformance 校验
        leaderboard.json
        __init__.py

## 将来 GitHub 建仓后一键推送

    git add -A && git commit -m "批次-FinAgentRank 评测引擎+SCORING+conformance+点星后端" && git push --set-upstream origin dev
