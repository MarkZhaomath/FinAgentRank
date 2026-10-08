"""FinAgentRank · 步骤3 演示：SCORING 正式化。

运行：cd FinAgentRank && python src/finagentrank/run_step3.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from finagentrank.scoring import SCORING, CLASS_WEIGHTS, DEFAULT_TOL
from finagentrank.score import (
    EvalAgent, FAMILIES, INSUFFICIENT, Metric, build_demo_agents, leaderboard_json,
)


def main() -> None:
    print("===== SCORING 正式规则（scoring.py 单一事实来源）=====")
    print(f"  C1–C4 权重 = {CLASS_WEIGHTS}（默认均权）")
    print(f"  容差 tol   = {DEFAULT_TOL}")
    print(f"  n_min = {SCORING['n_min']}（某族观测不足 → 标 insufficient，不给分）")
    print(f"  入榜门槛 = 能力分≥{SCORING['pass']['capability_min']} 且 CI半宽≤{SCORING['pass']['ci_width_max']}")

    print("\n===== 1) n_min 不足 → insufficient =====")
    sparse = EvalAgent("SparseAgent", False)
    sparse.metrics["Factor"] = {"C1": Metric([0.9]), "C2": Metric([0.8])}  # 仅 2 个观测
    row = sparse.leaderboard_row(rng_seed=1)
    print(f"  Factor 族观测不足(<{SCORING['n_min']}) → per_family['Factor'] = "
          f"{row['per_family'].get('Factor')} → {'insufficient ✓' if str(row['per_family'].get('Factor'))=='insufficient' else '失败'}")

    print("\n===== 2) 入榜门槛判定 =====")
    agents = build_demo_agents()
    lb = leaderboard_json(agents)
    for r in lb["agents"]:
        print(f"  {r['name']:<18} cap={r['capability']} CI半宽={(r['ci_high']-r['ci_low'])/2:.2f} "
              f"最强={r['top_family']:<8} 状态={r['status']}")
    official = [r for r in lb["agents"] if r["status"] == "official"]
    print(f"\n  正式档 {len(official)}/{len(lb['agents'])} 达标 → 其余为 provisional（过门槛才 official）")


if __name__ == "__main__":
    main()
