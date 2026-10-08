"""FinAgentRank 评测引擎 · 端到端跑一次。

运行：cd FinAgentRank && python src/finagentrank/run_demo.py
输出：capability 分数 + 95% CI + leaderboard.json（与前端同构）。
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from finagentrank.score import (
    FAMILIES, build_demo_agents, leaderboard_json,
    replicate_score, correlation_score, walk_forward_split,
)


def main() -> None:
    agents = build_demo_agents()

    # 1) C1 客观复算 / C2 因子复算 快速自检
    print("===== 快速自检：容差复算 + 因子相关 =====")
    print(f"  C1 精确复算(误差 0.02) → {replicate_score(10.0, 10.02):.3f} (应≈1.0)")
    print(f"  C1 误差 0.15 → {replicate_score(10.0, 10.15):.3f} (应衰减)")
    pred = [i * 0.9 + random_noise(i) for i in range(50)]
    ref  = [i * 0.9 for i in range(50)]
    print(f"  C2 因子相关(近线性) → {correlation_score(pred, ref):.3f} (应≈0.95+)")

    # 2) walk-forward 时序切分
    tr, te = walk_forward_split(100)
    print(f"\n===== walk-forward 时序切分 =====\n  训练 {len(tr)} 期 · 样本外 {len(te)} 期（防前视）")

    # 3) 能力分 + CI + 排行榜
    print("\n===== 排行榜（能力分 ± 95% CI · 样本外）=====")
    lb = leaderboard_json(agents)
    for i, r in enumerate(lb["agents"], 1):
        dog = " (dogfood)" if r["dogfood"] else ""
        print(f"  #{i:<2} {r['name']:<18}{dog}  {r['capability']:.2f} "
              f"[{r['ci_low']:.2f}-{r['ci_high']:.2f}]  最强={r['top_family']}")

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leaderboard.json")
    with open(out, "w") as f:
        json.dump(lb, f, ensure_ascii=False, indent=2)
    print(f"\n→ 已写 {out}（前端 FinAgentRank-web 可同构替换 mock）")

    # 4) 验证：第一名应高于坏/漂移 Agent；自动分类应命中各 Agent 的专精族
    top = lb["agents"][0]["capability"]
    bad = next(a["capability"] for a in lb["agents"] if a["name"] == "NoisyAgent")
    ok_order = top > bad
    # 自动分类命中检查：专精族应成为该 Agent 的"最强族"
    hits = all(
        next(a for a in lb["agents"] if a["name"] == n)["top_family"] == fam
        for n, fam in [("AlphaFactor-Quant", "Factor"), ("ETF-Guard", "Risk"),
                       ("SentimentEdge", "Signal")]
    )
    print(f"\n===== 验证 =====\n  第一名 {top:.2f} > 坏Agent {bad:.2f} → "
          f"{'通过' if ok_order else '未通过'}")
    print(f"  自动分类命中专精族(因子/风控/信号) → {'通过' if hits else '未通过'}")


def random_noise(i: int) -> float:
    import random
    return random.Random(i).uniform(-0.05, 0.05)


if __name__ == "__main__":
    main()
