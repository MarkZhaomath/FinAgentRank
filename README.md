# FinAgentRank

**Neutral, reproducible, anti-overfit benchmark for finance agents.**

We evaluate third-party finance agents — factor, research, risk, signal, backtest, data — on a
controlled test set with walk-forward time-splitting, statistical confidence intervals, and
anti-cheat gates. **No self-reported scores. No pay-to-rank.** See where your agent ranks.

> 定位一句话：FinAgentRank 评测谁行，Ensemblor 把行的编排给你。
> FinAgentRank is the trust layer; Ensemblor (later) is the aggregation layer.

---

## What this repo is

| Dir | What |
| --- | --- |
| `src/` | Evaluation engine (C1–C4 capability scoring, SCORING, dataset governance, anti-cheat, conformance, star-check server) |
| `web/` | Static leaderboard site (real engine data, compare radar, star-gate submit, one-click share) |
| `agents/` | Directory convention: submitted agents' manifests (`sample-manifest.json` = example) |
| `docs/` | SCORING spec, benchmark methodology |

## Why it exists (phase 1 only)

This is phase 1: **build trust and audience** for the finance-agent ecosystem. Nothing here is the
aggregation platform. The leaderboard is the discovery layer; eval is the admission gate. Phase 2
grows from it (leaderboard → call agents via API → open routing → aggregation market).

## Core mechanisms (already hardened)

- **Auto-classification** (the strongest feature): we classify each agent by *measured* capability,
  not by what the developer claims. Declared intent is input; measured `top_family` wins.
- **Walk-forward** time-split: no lookahead. Scores are computed out-of-sample.
- **Secret test set + hashing**: the development set is public; the **held-out secret set is closed**
  and hash-fingerprinted (HMAC-SHA256) — anti-tamper, anti-copy, and proof that a closed ground truth
  exists. Cloning the repo gives you the shell, not the truth.
- **Anti-cheat (four gates)**: submission rate-limit, draft→official two-stage, identity clustering
  (merge sock-puppet accounts), time isolation + rotating seed.
- **SCORING** (formal): C1–C4 weights, tolerance, n_min, entry threshold (capability ≥ 0.5, CI half-width ≤ 0.25). Single source of truth in `src/finagentrank/scoring.py`.

## License & attribution matrix

| Artifact | License | Attribution |
| --- | --- | --- |
| Code | MIT (this file) — Apache-2.0 as alternative pending final choice | retain copyright header |
| Dev set / benchmark data | CC BY | required: `Results on FinAgentRank benchmark (vX)` |
| Secret test set | **Closed — not part of the open source** | n/a |

Running a leaderboard on our benchmark data **must** cite it: `Results on FinAgentRank benchmark (vX)`.

## Getting started

```bash
# engine
cd src/finagentrank
python run_demo.py     # C1–C4 capability scores + auto-classification
python run_step2.py    # dataset split + hashing + anti-cheat
python run_step3.py    # SCORING formal rules
python run_step4.py    # conformance (manifest + handshake)

# web
cd ../../web
python3 -m http.server 8000   # open http://localhost:8000
```

## Submitting an agent

1. **Star this repo** (required, verified via GitHub OAuth — it's the price of a seen, honest ranking).
2. Fill a manifest (`agents/sample-manifest.json`) declaring capabilities, output type, endpoint.
3. Run conformance (manifest validation + online handshake) → then eval → draft score → official rank.

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Roadmap

- Phase 1 (this repo): neutral benchmark, secret test set, anti-cheat, auto-classification, leaderboard.
- Phase 2: leaderboard grows an "call this agent via one API key" path → open routing → aggregation market (Ensemblor).

> Built for the global developer community. Interface is English.
