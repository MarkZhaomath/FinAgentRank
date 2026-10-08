"""FinAgentRank · SCORING 正式评分规则（单一事实来源 · 步骤3）。

对应白皮书 §9「三层打分 SCORING」的落地。所有判分参数在此定义，score.py 读取，
避免散落硬编码。默认能力权重均权、容差分 能力设定（可配置，改动须进白皮书征求意见）。

- classes：C1–C4 判分（weight / 容差 tol / 名目）。
- n_min：某能力族有效观测数下限，不足标记 insufficient（不静默给分）。
- ci：bootstrap 置信区间参数。
- walk_forward：时序切分。
- pass：入榜/正式档的硬门槛（capability 下限 + CI 宽度上限）。
"""

SCORING = {
    "classes": {
        "C1": {"name": "客观复算", "weight": 0.25, "tol": 0.05,
                "desc": "输出与 ground-truth 在容差内匹配（口径/精确）"},
        "C2": {"name": "因子复算", "weight": 0.30, "tol": 0.05,
                "desc": "因子/信号输出与参考序列相关（相关度≥0.8 记满分档）"},
        "C3": {"name": "稳健性",   "weight": 0.20, "tol": 0.05,
                "desc": "跨 seed / regime 低方差（相对波动，越小越稳）"},
        "C4": {"name": "决策支持", "weight": 0.25, "tol": 0.05,
                "desc": "校准 / 覆盖率（输出可解释、区间覆盖实测）"},
    },
    "n_min": 3,              # 某族至少 n_min 个有效观测才给分，否则 insufficient
    "n_min_display": 3,
    "ci": {"n_boot": 500, "level": 0.95},
    "walk_forward": {"train_frac": 0.7},
    "pass": {
        "capability_min": 0.50,    # 入榜/正式档能力分下限
        "ci_width_max": 0.25,      # CI 半宽上限（过宽 = 数据不足，降权/不出正式档）
    },
}

# 便捷取用
CLASS_WEIGHTS = {k: v["weight"] for k, v in SCORING["classes"].items()}
DEFAULT_TOL = {k: v["tol"] for k, v in SCORING["classes"].items()}
