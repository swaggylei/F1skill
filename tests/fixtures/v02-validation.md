# v0.2 live validation — 2026-11-19

Live validation artifacts are stored outside the checkout at `/workspace/scratch/f1-v02-baseline-2024` in the development environment. They are not bundled official archives or a portable approved database.

- 2024: 24 GP classifications and awarded-points tables compared with Formula1.com; all matched after explicit handling of Zhou's name order and disqualified entries in non-classified ordering.
- Live Jolpica resync completed silently with review history retained. This tests persistence under identical facts, not legal correctness.
- FIA indices collected for all 24 events. Final GP classification PDFs found for 23 events; year/event identity and podium comparison passed for all 23.
- The Mexico City event index exposed a provisional race classification but no final race-classification link at retrieval. This is a recorded source gap, not proof that no final document exists elsewhere.
- FIA documents/decisions have not been comprehensively adjudicated for open appeals. All collected packets retain `decision_clearance: unreviewed`. No synthetic manual confirmation was applied to real data.
- Independent capability reviews, mixed claim statuses, stale-fact invalidation, unchanged-review deduplication, year/event mismatch rejection and persistence are tested with synthetic evidence. Synthetic evidence cannot establish real historical records.

Results describe retrieved evidence at validation time. A new or amended document must be reviewed and retained as a new evidence version.
