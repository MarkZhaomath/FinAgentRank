# FinAgentRank

**A neutral, reproducible, anti-overfit benchmark for finance agents.**

> See where your finance agent actually ranks — not where it claims to.
> No self-reported scores. No pay-to-rank. Just measured capability.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](#getting-started)
![Status](https://img.shields.io/badge/status-phase--1--benchmark-informational)

---

## Why we built this

Finance AI is fragmenting fast. Indie developers and small quant teams are shipping agents for
factors, research, risk, signals, and backtesting — and everyone says theirs is the best. But nobody
can tell you which one is *actually* good, because **everyone self-reports**.

FinAgentRank is the neutral referee: a controlled, reproducible test set with walk-forward
time-splitting, statistical confidence intervals, anti-cheat gates, and **auto-classification by
measured capability** — not by what a developer *claims*.

**The hook:** *Submit your agent, get an instant draft score, see where you stand — and share your
rank.*

---

## What makes it trustworthy

| Mechanism | What it means |
| --- | --- |
| **Secret test set, hash-fingerprinted** | The dev set is public; the held-out **secret set is closed** (HMAC-SHA256). Anti-tamper, anti-copy, and proof a real ground truth exists. Cloning the repo gives you the shell, not the truth. |
| **Walk-forward time-splitting** | No lookahead. Scores are computed strictly out-of-sample. |
| **Statistical confidence** | Bootstrap 95% CI per score. CI overlap = tie — no false "#1". |
| **Auto-classification** | We classify each agent by *measured* performance, not by what you claim. Declared intent is input; measured `top_family` wins. |
| **Anti-cheat, four gates** | Submission rate-limit · draft→official two-stage · identity clustering (merges sock-puppet accounts) · time isolation + rotating seed. |
| **No pay-to-rank, ever** | Ranking is by measured capability + confidence only. That's the whole point. |

---

## Get started

```bash
git clone https://github.com/MarkZhaomath/FinAgentRank.git
cd FinAgentRank

# run the evaluation engine
cd src/finagentrank
python run_demo.py     # C1–C4 capability scores + auto-classification
python run_step2.py    # dataset split + hashing + anti-cheat
python run_step3.py    # SCORING formal rules
python run_step4.py    # conformance (manifest + handshake)

# view the leaderboard
cd ../../web
python3 -m http.server 8000    # open http://localhost:8000
```

**Live leaderboard:** the site renders real engine output from `web/leaderboard.json`.

---

## Submit your agent

1. **Star this repo** — required, verified via GitHub OAuth. It's the price of a ranking that actually gets seen.
2. Fill a manifest (`agents/sample-manifest.json`): capabilities, output type, endpoint.
3. Conformance check (manifest validation + online handshake) → eval → draft score → official rank.

> We **call your API**; we never execute your code. The security boundary is on the network layer.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full flow.

---

## Repo layout

| Path | What |
| --- | --- |
| `src/finagentrank/` | Evaluation engine: SCORING, dataset governance, anti-cheat, conformance, star-check server |
| `web/` | Static leaderboard site (real engine data, compare radar, star-gate submit, one-click share) |
| `agents/` | Directory convention for submitted manifests (`sample-manifest.json` = example) |
| `docs/SCORING.md` | Formal scoring rules (single source of truth: `src/finagentrank/scoring.py`) |

---

## License & attribution

| Artifact | License | Attribution |
| --- | --- | --- |
| Code | MIT | retain copyright header |
| Dev set / benchmark data | CC BY | required: `Results on FinAgentRank benchmark (vX)` |
| Secret test set | **Closed** — not part of the open source | n/a |

Running a leaderboard on our benchmark data **must** cite it:
`Results on FinAgentRank benchmark (vX)`.

---

## Contributing

We welcome finance agents to be benchmarked and developers to improve the harness. Open an issue,
or start a Discussion. Read [CONTRIBUTING.md](CONTRIBUTING.md) first.

> Built for the global developer community. English interface.
