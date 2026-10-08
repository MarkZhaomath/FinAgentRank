"""FinAgentRank · 数据集治理模块（步骤2 之一）。

对应白皮书 §8「保密测试集不公开；防过拟合 / 防抄底 / 可哈希」+ 调研引擎1（防污染三道防线）。

- split_dataset：测试题切分成【公开开发集】+【封闭保密测试集】（可设 embargo 时间间隔）。
- hash_testset：保密测试集的可哈希指纹（HMAC-SHA256，逐项+盐 → 集指纹）。用途：
    ① 防篡改（榜单引用某一版测试集，指纹可对账）
    ② 抄底检测（同一版题被偷用，靠指纹发现"用我题却不署名"）
    ③ 向外界证明"我有一套封闭真值"（发布指纹，不发布题）。
- item_fingerprint / jaccard：MinHash 式 n-gram 指纹，近重复/抄底扫描（提交的题 vs 公开语料）。
纯标准库。
"""

from __future__ import annotations

import hashlib
import hmac
import random
import re
from typing import Sequence


def split_dataset(
    ids: Sequence[str],
    seed: int = 2026,
    secret_frac: float = 0.30,
) -> tuple[list[str], list[str]]:
    """按 seed 打乱后切分：公开开发集 + 封闭保密测试集。

    - 开发集 (dev)：公开，开发者可自测（草稿分）。
    - 保密集 (secret)：封闭，只用于正式排名（反过拟合命门）。
    - secret_frac：保密占比（默认 30%）。
    返回 (dev_ids, secret_ids)。
    """
    rng = random.Random(seed)
    idx = list(range(len(ids)))
    rng.shuffle(idx)
    cut = int(len(ids) * (1 - secret_frac))
    return [ids[i] for i in idx[:cut]], [ids[i] for i in idx[cut:]]


def hash_testset(items: Sequence[str], salt: str = "finagentrank-v0") -> str:
    """保密测试集的可哈希指纹。

    对每项先 HMAC-SHA256（加盐，防彩虹表枚举），再串进集指纹。
    同一个盐 + 同一份题 → 恒等指纹；题目增删/改 → 指纹变化（防篡改可对账）。
    """
    digest = hashlib.sha256()
    for it in items:
        token = hmac.new(salt.encode(), str(it).encode(), hashlib.sha256).digest()
        digest.update(token)
    return digest.hexdigest()


def item_fingerprint(text: str, shingles: int = 5) -> set[str]:
    """MinHash 式 n-gram 指纹：把文本切成 shingle 集合，用于近重复/抄底检测。

    返回字符 n-gram 集合（小写、去空白）。两段文本越相似，Jaccard 越高。
    """
    text = re.sub(r"\s+", " ", text.strip().lower())
    grams: set[str] = set()
    for i in range(len(text) - shingles + 1):
        grams.add(text[i:i + shingles])
    return grams


def jaccard(a: set[str], b: set[str]) -> float:
    """Jaccard 相似度（0=无关，1=完全重复）。"""
    inter, union = len(a & b), len(a | b)
    return inter / union if union else 0.0


def near_duplicate_rate(submission_texts: Sequence[str], corpus_texts: Sequence[str], thr: float = 0.7) -> list[tuple[str, str, float]]:
    """抄底/近重复扫描：每个提交 vs 公开语料，标记 Jaccard≥thr 的对（嫌疑）。

    返回 [(提交文本, 命中语料文本, 相似度)]。
    """
    subs = [(t, item_fingerprint(t)) for t in submission_texts]
    corp = [(t, item_fingerprint(t)) for t in corpus_texts]
    hits = []
    for t1, f1 in subs:
        for t2, f2 in corp:
            sim = jaccard(f1, f2)
            if sim >= thr:
                hits.append((t1, t2, round(sim, 2)))
    return hits
