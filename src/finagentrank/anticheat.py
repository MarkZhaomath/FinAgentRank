"""FinAgentRank · 防作弊四件套（步骤2 之二）。

对应 §12.3「草稿/正式两级（防作弊）」+ 调研引擎1（提交限流/指纹去重/身份聚类/时间隔离）。

四件套（每一项都可机判定）：
  ① 提交限流 + 最低门槛  —— 单账号窗口内次数上限；正式档需先有草稿积累。
  ② 草稿 → 正式两级      —— 草稿分即时出（低成本、易被刷），正式分需过完整门槛（防刷）。
  ③ 身份聚类 / 去重小号    —— 指纹 / IP 聚类合并疑似小号，防"一稿多投刷榜"。
  ④ 时间隔离 + 轮换 seed  —— 测试题生成时间必须晚于模型训练截止（防前视）；季度轮换 secret seed。
纯标准库，可单测。
"""

from __future__ import annotations

import collections
import time
from typing import DefaultDict


# ---------- ① 提交限流 + 门槛 ----------

class SubmissionLimiter:
    """按账号 + 滑窗限流。window_s 秒内最多 max_per_window 次正式提交。"""

    def __init__(self, max_per_window: int = 3, window_s: int = 3600):
        self.max = max_per_window
        self.window = window_s
        self._ts: DefaultDict[str, list[float]] = collections.defaultdict(list)

    def allow(self, account_id: str, now: float = None) -> bool:
        now = now or time.time()
        q = self._ts[account_id]
        # 丢出窗口外的
        self._ts[account_id] = [t for t in q if now - t < self.window]
        if len(self._ts[account_id]) >= self.max:
            return False
        self._ts[account_id].append(now)
        return True


def meets_submission_threshold(draft_count: int, min_drafts: int = 2) -> bool:
    """正式档门槛：须先有足够草稿分积累（刷一次即给正式档的通道封死）。"""
    return draft_count >= min_drafts


# ---------- ② 草稿 → 正式两级 ----------

class DraftOfficialGate:
    """草稿档即时出分；正式档需 门槛 + 无异常 才放行。"""

    def __init__(self, min_drafts: int = 2):
        self.min_drafts = min_drafts
        self._drafts: DefaultDict[str, int] = collections.defaultdict(int)
        self._official: set[str] = set()

    def submit_draft(self, account_id: str) -> str:
        """草稿分（低成本，即时）。"""
        self._drafts[account_id] += 1
        return "draft"

    def try_official(self, account_id: str, anomaly_free: bool) -> tuple[bool, str]:
        """正式档放行判定：草稿数达标 且 无异常（如限流超限、近重复命中）。"""
        if not anomaly_free:
            return False, "blocked: anomaly"
        if not meets_submission_threshold(self._drafts[account_id], self.min_drafts):
            return False, f"blocked: need {self.min_drafts} drafts"
        self._official.add(account_id)
        return True, "official"


# ---------- ③ 身份聚类 / 去重小号 ----------

class IdentityClustering:
    """用共享指纹 / IP 聚类合并疑似小号，防一稿多投刷榜。

    规则（工程简化）：同指纹不同账号 → 判定同源；同源累计投票超过上限 → 只计 1。
    """

    def __init__(self, max_votes_per_cluster: int = 1):
        self.max_votes = max_votes_per_cluster
        self._finger_to_accounts: DefaultDict[str, list[str]] = collections.defaultdict(list)

    def register(self, account_id: str, fingerprint: str) -> str:
        """登记一次"投榜"，返回是否被当作独立有效票。"""
        self._finger_to_accounts[fingerprint].append(account_id)
        cluster = self._finger_to_accounts[fingerprint]
        # 同源超过阈值 → 第 1 票算有效，其余判小号合并
        if len(cluster) > self.max_votes:
            return "merged-small-account"
        return "counted"


# ---------- ④ 时间隔离 + 轮换 seed ----------

def time_isolation_ok(item_gen_ts: float, model_cutoff_ts: float) -> bool:
    """时间隔离：测试题生成时间必须晚于模型训练截止（否则前视泄漏）。

    例：Agent 训练截止 2026-06-30，2026-09-01 生成的题才可入正式榜。
    """
    return item_gen_ts > model_cutoff_ts


def rotation_seed(quarter: int, base_seed: int = 2026) -> int:
    """季度轮换 seed：每季度换一个秘密 seed，公开题不定期轮换防污染。"""
    return base_seed + quarter * 7
