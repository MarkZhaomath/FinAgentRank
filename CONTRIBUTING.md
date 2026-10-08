# Contributing — Submit a finance agent to the benchmark

We evaluate **third-party finance agents** and publish a neutral leaderboard. The eval is objective,
reproducible, and anti-overfit. Here's how to get your agent on it.

## Before you start

- **Star this repo.** Submitting requires it (verified via GitHub OAuth). It's the price of a ranking
  that actually gets seen — and it's the only "payment" we ask.
- Your agent must be reachable as an API endpoint. We **call your API**; we never execute your code.
  This keeps the security boundary on the network layer.

## 1. Fill a manifest

Copy `agents/sample-manifest.json` and fill it in. Required fields:

| Field | Meaning |
| --- | --- |
| `name` | Human name |
| `name_for_model` | Machine-safe identifier |
| `endpoint` | `https://` base URL (we hit `{endpoint}/health` for the handshake) |
| `auth` | `bearer` or `none` |
| `capabilities` | What you *intend* to do (Data / Factor / Research / Risk / Signal / Backtest) |
| `output_type` | One of `research | signal | data | risk | backtest | factor` |
| `egress_hosts` | Data sources you call (e.g. `yfinance`, `edgar`) |
| `schema_version` | `0.1` |

> Your declared capabilities are an **intent signal only**. After eval we auto-classify you by
> **measured** performance (`top_family`). If your declared class and your measured class disagree,
> measured wins — and we tell you.

## 2. Run the conformance check

The submit form (or `POST /api/conformance`) validates the manifest and does an **online handshake**
to your endpoint. If it fails, we return specific fix suggestions. Pass = your agent enters the eval queue.

## 3. Eval → draft → official

1. **Draft score**: quick, low-cost — you see where you stand within minutes.
2. **Official score**: full anti-cheat run (rate-limit, draft-history threshold, identity dedup,
   time isolation). Pass the entry threshold (capability ≥ 0.5, CI half-width ≤ 0.25) → official rank.

## Fair-play rules

- No pay-to-rank. Ranking is by measured capability + confidence interval only.
- No self-reported scores. We compute everything.
- The **secret test set** is closed. Overfitting against the public dev set will show up on the
  held-out set — that's the point.
- Running a leaderboard on our benchmark **data** must cite it:
  `Results on FinAgentRank benchmark (vX)`.

## Questions

Open an issue. Keep it civil — the whole point is building a trusted ecosystem.
