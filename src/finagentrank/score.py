"""FinAgentRank 客观评测引擎核心（C1–C4 能力分）。

对应白皮书 §9/§13/§16 与调研引擎1。要点：
- 能力分按 TAXONOMY 能力族计算（这里 6 族简化示意）。
- C1–C4 = 四类客观评测：C1 客观复算(口径/精确) · C2 因子复算(信号/相关) ·
  C3 稳健性(跨 seed/regime 低方差) · C4 决策支持(校准/覆盖率)。
- 每类给 0–1 子分，按权重合成能力分；bootstrap 出 95% CI。
- walk-forward 强制时序切分（样本外计分，防前视）。
- 输出 leaderboard JSON（与前端 FinAgentRank-web 同构可替换）。
纯 Python 标准库，无依赖。
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field

# TAXONOMY 能力族（简化 6 族；正式版 4 层 14 类）
FAMILIES = ["Data", "Factor", "Research", "Risk", "Signal", "Backtest"]

# 正式评分规则（scoring.py 单一事实来源）
from finagentrank.scoring import SCORING, CLASS_WEIGHTS
N_MIN = SCORING["n_min"]
PASS_MIN = SCORING["pass"]["capability_min"]
CI_MAX = SCORING["pass"]["ci_width_max"]
INSUFFICIENT = -1.0  # 观测不足的哨兵值（标记 insufficient，不给分）


@dataclass
class Metric:
    """Agent 在某能力族某评测类上的观测值集合（多次运行 → 可做稳健性/CI）。"""
    values: list[float] = field(default_factory=list)


def replicate_score(expected: float, observed: float, tol: float = 0.05) -> float:
    """容差判定：|expected-observed| 在 tol 内满分，线性衰减，越界归 0。"""
    d = abs(expected - observed)
    if d <= tol:
        return 1.0
    if d <= 3 * tol:
        return max(0.0, 1.0 - (d - tol) / (2 * tol))
    return 0.0


def correlation_score(pred: list[float], ref: list[float]) -> float:
    """因子/信号复算：Pearson 相关（无响应→0）。"""
    n = len(pred)
    if n < 2:
        return 0.0
    mpx, mpy = sum(pred) / n, sum(ref) / n
    num = sum((pred[i] - mpx) * (ref[i] - mpy) for i in range(n))
    dx = math.sqrt(sum((x - mpx) ** 2 for x in pred)) or 1e-9
    dy = math.sqrt(sum((y - mpy) ** 2 for y in ref)) or 1e-9
    return max(0.0, min(1.0, num / (dx * dy)))


def _bootstrap_ci(scores: list[float], n_boot: int = 500, seed: int = 0) -> tuple[float, float, float]:
    """mean 与 bootstrap 95% CI（下界, 上界）。"""
    rng = random.Random(seed)
    mean = sum(scores) / len(scores)
    if len(scores) < 2:
        return mean, mean, mean
    boot = []
    for _ in range(n_boot):
        s = [rng.choice(scores) for _ in scores]
        boot.append(sum(s) / len(s))
    boot.sort()
    lo, hi = boot[int(0.025 * n_boot)], boot[int(0.975 * n_boot)]
    return mean, lo, hi


@dataclass
class EvalAgent:
    name: str
    dogfood: bool = False
    # 每能力族每评测类的指标：metrics[fam][cls] = Metric(values)
    metrics: dict = field(default_factory=dict)

    def capability(self, fam: str) -> float:
        """单能力族能力分 = C1..C4 按正式权重加权；观测不足(<n_min)则 insufficient。"""
        tot, wsum, obs_count = 0.0, 0.0, 0
        for cls, w in CLASS_WEIGHTS.items():
            vals = self.metrics.get(fam, {}).get(cls, Metric([])).values
            if vals:
                tot += w * (sum(vals) / len(vals))
                wsum += w
                obs_count += len(vals)
        if wsum == 0 or obs_count < N_MIN:
            return INSUFFICIENT
        return tot / wsum

    def leaderboard_row(self, rng_seed: int = 0) -> dict:
        """合成总能力分（各族平均）+ bootstrap CI + 最强族 + 入榜门槛判定。

        入榜/正式档门槛（scoring.py）：能力分≥PASS_MIN 且 CI 半宽≤CI_MAX。
        观测不足的族标 insufficient（不参与总能力分）。
        """
        per_fam = {}
        for fam in FAMILIES:
            v = self.capability(fam)
            if v > INSUFFICIENT:
                per_fam[fam] = v
        scores = list(per_fam.values())
        if not scores:  # 各族都观测不足 → 不给分
            return {"name": self.name, "dogfood": self.dogfood,
                    "capability": 0.0, "ci_low": 0.0, "ci_high": 0.0,
                    "top_family": None, "per_family": {"Factor": "insufficient"},
                    "status": "provisional"}
        mean, lo, hi = _bootstrap_ci(scores, seed=rng_seed)
        top_fam = max(per_fam, key=lambda f: per_fam[f]) if per_fam else None
        ci_half = (hi - lo) / 2
        qualifies = (mean >= PASS_MIN) and (ci_half <= CI_MAX)
        return {
            "name": self.name,
            "dogfood": self.dogfood,
            "capability": round(mean, 3),
            "ci_low": round(lo, 3),
            "ci_high": round(hi, 3),
            "top_family": top_fam,
            "per_family": {f: (round(v, 3) if v > INSUFFICIENT else "insufficient")
                           for f, v in per_fam.items()},
            "status": "official" if qualifies else "provisional",
        }


def walk_forward_split(series_len: int, train_frac: float = 0.7) -> tuple[range, range]:
    """强制时序切分：前 train_frac 训练、后样本外测试（防前视）。"""
    cut = int(series_len * train_frac)
    return range(0, cut), range(cut, series_len)


def build_demo_agents() -> dict[str, EvalAgent]:
    """构造 mock 评测数据：每个 Agent 专精不同能力族（用于演示"自动分类"）。

    每个 Agent 给一个 specialty 族（高分）+ 其他族一般分；NoisyAgent 全面弱，
    DriftAgent 跨 seed 不稳（C3 稳健性被扣）。这是 mock，正式接入用真实评测。
    """
    def mk(specialty: str, strong=0.9, weak=0.7, noise=0.02, n_seed=5, drift=0.0):
        rng = random.Random(hash(specialty) & 0xffff)
        out = {}
        for fi, fam in enumerate(FAMILIES):
            base = strong if fam == specialty else weak
            out[fam] = {}
            for cls in ("C1", "C2", "C3", "C4"):
                vals = []
                for s in range(n_seed):
                    v = base + rng.uniform(-noise, noise) - drift * s
                    vals.append(max(0.0, min(1.0, v)))
                out[fam][cls] = Metric(values=vals)
        return out

    return {
        "AlphaFactor-Quant": EvalAgent("AlphaFactor-Quant", False, mk("Factor", 0.92, 0.68, noise=0.015)),
        "ETF-Guard":         EvalAgent("ETF-Guard", True,     mk("Risk", 0.92, 0.70, noise=0.018)),
        "ETF-Race":          EvalAgent("ETF-Race", True,      mk("Factor", 0.88, 0.68, noise=0.02)),
        "SentimentEdge":     EvalAgent("SentimentEdge", False, mk("Signal", 0.86, 0.66, noise=0.03)),
        "RiskShield":        EvalAgent("RiskShield", False,   mk("Risk", 0.88, 0.68, noise=0.025)),
        "NoisyAgent":        EvalAgent("NoisyAgent", False,   mk("Factor", 0.62, 0.55, noise=0.12)),
        "DriftAgent":        EvalAgent("DriftAgent", False,   mk("Signal", 0.82, 0.65, noise=0.02, drift=0.03)),
    }


def leaderboard_json(agents: dict[str, EvalAgent]) -> dict:
    rows = [a.leaderboard_row(rng_seed=i) for i, a in enumerate(agents.values())]
    rows.sort(key=lambda r: -r["capability"])
    return {"families": FAMILIES, "agents": rows, "schema_version": "0.1"}
