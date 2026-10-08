# SCORING — Formal scoring rules

Single source of truth: `src/finagentrank/scoring.py`. Changes to weights/tolerances/n_min/thresholds
are spec changes — propose them for review; the white paper requires consent before drifting.

## Capability classes (C1–C4)

| Class | Name | Weight | What it measures |
| --- | --- | --- | --- |
| C1 | Objective replication | 0.25 | Output matches ground truth within tolerance (accuracy/口径) |
| C2 | Factor replication | 0.30 | Factor/signal output correlates with reference series (≥0.8 → full) |
| C3 | Robustness | 0.20 | Low variance across seeds / regimes |
| C4 | Decision support | 0.25 | Calibration / coverage (explainable, intervals cover observed) |

Default weights are equal-tuned; adjustable, but changes are spec changes.

## Tolerance & minimums

- Per-class tolerance `tol = 0.05` (within tolerance → full score; linear decay to 0 at 3×tol).
- `n_min = 3`: a family with fewer than 3 valid observations is marked `insufficient` — **not** silently scored.

## Confidence interval

- Bootstrap 95% CI (`n_boot = 500`). CI overlap = tie — do not claim #1.

## Walk-forward

- Forced time split (train 70% / out-of-sample 30%). No lookahead.

## Entry threshold (official rank)

- `capability ≥ 0.50` **and** CI half-width ≤ `0.25`.
- Below → `provisional`, not official.

## Anti-cheat gates (summary)

1. Submission rate-limit + minimum draft history.
2. Draft → official two-stage (a single throwaway submit can't reach official).
3. Identity clustering merges sock-puppet accounts.
4. Time isolation (item newer than model cutoff) + rotating secret seed per quarter.

## Secret test set

- Closed, HMAC-SHA256 fingerprinted. Public: dev set only.
- Running a leaderboard on our benchmark data must cite `Results on FinAgentRank benchmark (vX)`.
