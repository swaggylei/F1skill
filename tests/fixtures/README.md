# Historical replay sample

`2024-opening.json` contains a small factual extraction of the 2024 Bahrain and Saudi Arabian GP classifications and actual starting grids from these pages, accessed 2026-11-17:

- https://www.formula1.com/en/results/2024/races/1229/bahrain/race-result
- https://www.formula1.com/en/results/2024/races/1229/bahrain/starting-grid
- https://www.formula1.com/en/results/2024/races/1230/saudi-arabia/race-result
- https://www.formula1.com/en/results/2024/races/1230/saudi-arabia/starting-grid

The table facts were extracted for regression tests; source page prose/HTML is not bundled. Source data retain their respective rights. Constructor IDs are explicitly mapped from the displayed teams; driver IDs use normalized full names for this two-race fixture (they are not a Jolpica identity crosswalk).

Birth dates are deliberately null because these result pages do not establish them. Both races remain provisional in the tracker: this sample does not include FIA decision review or independent historical comparison. The scope is only these two GPs, not the complete season or all-time records. These are the pages' current classifications, not as-issued archived versions; they do not test how a live run would have handled an old appeal. Synthetic correction tests cover revision mechanics separately.

The expected checks include Verstappen's two in-scope wins, Red Bull's four podium places and two one-twos, seven days between wins, and Zhou's six-place gain in Bahrain (grid P17 to result P11). They provide a small real-data arithmetic check, not validation of the live Jolpica endpoint or the whole historical record catalogue.
