"""FinAgentRank · 步骤2 演示：开发集/保密集切分 + 哈希 + 防作弊四件套。

运行：cd FinAgentRank && python src/finagentrank/run_step2.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from finagentrank.anticheat import (
    DraftOfficialGate, IdentityClustering, SubmissionLimiter,
    rotation_seed, time_isolation_ok,
)
from finagentrank.dataset import (
    hash_testset, item_fingerprint, jaccard, near_duplicate_rate, split_dataset,
)


def main() -> None:
    # ---- 1) 开发集 / 保密集切分 ----
    items = [f"item-{i}" for i in range(100)]
    dev, secret = split_dataset(items, seed=42, secret_frac=0.3)
    assert set(dev) & set(secret) == set(), "切分不应重叠"
    print("===== 1) 开发集 / 保密集切分 =====")
    print(f"  开发集(公开) {len(dev)} 项 · 保密集(封闭) {len(secret)} 项 · 无重叠 ✓")

    # ---- 2) 保密集可哈希（防篡改/抄底/证明真值）----
    h1 = hash_testset(secret, salt="v1")
    h2 = hash_testset(secret, salt="v1")            # 同盐同题 → 恒等
    h3 = hash_testset(secret[: len(secret) - 1], salt="v1")  # 改一题 → 指纹变
    print("\n===== 2) 保密集可哈希指纹 =====")
    print(f"  指纹(恒等)  {h1[:16]}… == {h2[:16]}… → {'一致✓' if h1 == h2 else '失败'}")
    print(f"  增删一题后  {h1[:16]}… != {h3[:16]}… → {'防篡改✓' if h1 != h3 else '失败'}")
    print(f"  用途：发布指纹不发布题 → 向外界证明'有一套封闭真值'；榜单对账防篡改")

    # ---- 3) MinHash 指纹近重复 / 抄底 ----
    orig = "the financial report shows revenue growing by 12 percent quarter over quarter"
    leak = "the financial report shows revenue growing by 12 percent quarter over quarter"
    other = "central banks adjust interest rates to control inflation and growth"
    sim = jaccard(item_fingerprint(orig), item_fingerprint(leak))
    hits = near_duplicate_rate([leak], [orig, other], thr=0.6)
    print("\n===== 3) 指纹近重复 / 抄底检测 =====")
    print(f"  原题 vs 泄漏题 Jaccard = {sim:.2f} → {'抄底嫌疑✓' if hits else '失败'}")
    print(f"  命中 {len(hits)} 处 · 相似度 {hits[0][2] if hits else '-'}")

    # ---- 4) 防作弊四件套 ----
    print("\n===== 4) 防作弊四件套 =====")
    # ① 限流
    lim = SubmissionLimiter(max_per_window=3, window_s=3600)
    ok1 = all(lim.allow("accA") for _ in range(3))
    ok2 = lim.allow("accA") is False
    print(f"  ① 提交限流：3 次允许、第 4 次拒绝 → {'通过✓' if ok1 and ok2 else '失败'}")
    # ② 草稿→正式
    gate = DraftOfficialGate(min_drafts=2)
    gate.submit_draft("accB"); gate.submit_draft("accB")
    official = gate.try_official("accB", anomaly_free=True)
    blocked = DraftOfficialGate(min_drafts=2).try_official("accC", anomaly_free=True)
    print(f"  ② 草稿→正式：达标放行={official[0]}({official[1]}) · 未达标拦截={not blocked[0]} → {'通过✓' if official[0] and not blocked[0] else '失败'}")
    # ③ 身份聚类
    idc = IdentityClustering(max_votes_per_cluster=1)
    v1 = idc.register("a", "fp-X")
    v2 = idc.register("b", "fp-X")   # 同指纹 → 小号合并
    print(f"  ③ 身份聚类：同指纹第2账号 = {v2} → {'合并小号✓' if v2 == 'merged-small-account' else '失败'}")
    # ④ 时间隔离 + 轮换 seed
    ts_ok = time_isolation_ok(1_700_000_000, 1_690_000_000)   # 题晚于截止 → 有效
    ts_bad = time_isolation_ok(1_600_000_000, 1_690_000_000)   # 题早于截止 → 前视
    seeds = [rotation_seed(q) for q in range(1, 5)]
    print(f"  ④ 时间隔离：晚于截止有效={ts_ok} · 早于截止拦截={not ts_bad} → "
          f"{'通过✓' if ts_ok and not ts_bad else '失败'}")
    print(f"    季度轮换 seed = {seeds} (每季不同 → 公开题轮换防污染)")


if __name__ == "__main__":
    main()
