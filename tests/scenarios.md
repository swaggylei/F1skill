# Behavioral acceptance scenarios

Use a temporary data directory and mocked dated official documents. Do not publish synthetic reports as real races.

| Input situation | Required behavior |
|---|---|
| Fresh install, several seasons available | Dated baseline; latest completed GP only unless catch-up requested; no invented before counts. |
| No new GP, all reviews unchanged | Run log updated, no routine notification. |
| Two missed GPs | Two chronological reports; second uses first's resulting state. |
| Sprint finished, GP not yet finished | No GP-weekend report; no Sprint added to GP wins. |
| Final classification with known unresolved appeal | Claims provisional; pending review retained. |
| Later DSQ alters podium and streak | Revised evidence, recomputed dependent claims, retained old revision, one correction. |
| Source timeout | Failure/gap recorded; no false no-new-race conclusion or successful event marker. |
| FIA landing page defaults to old season | Reject mismatched document; locate actual event. |
| Qualifying P1 starts P6 after penalty | Separate qualifying result, pole credit and grid; apply era convention. |
| Streak ends below historical maximum | ENDED STREAKS; do not claim historical record broken. |
| Equal maximum | Joint/tied record; not outright broken record. |
| Incomplete pre-1980 history | Bounded period claim or unverified candidate; no “first ever”. |
| Crash after report saved before state update | Recover existing report ID; avoid duplicate publication. |
| Same event/evidence processed twice | No second new-record report. |
| Renamed constructor | Explicit identity scope; no silent lineage merge. |
| English/bilingual request | Equivalent evidence and definitions in requested language. |

These are review fixtures, not claims of automated end-to-end testing.
