# Evidence verification v0.2

Run commands from the repository root with Python 3.10+. The original twenty GP metrics are retained. Reviews now live in an independent SQLite table (schema version 2); opening a v1 database adds the table without deleting observations, reports or delivery history. Back up important data first. Keep the full database for migrations; no downgrade is provided.

## Establish a bounded baseline

```bash
python3 -m f1tracker --data-dir /persistent/f1-data sync --start-year 2024 --end-year 2024
python3 -m f1tracker --data-dir /persistent/f1-data verify-season 2024
python3 -m f1tracker --data-dir /persistent/f1-data review-status
```

The official checker discovers Formula1.com race-result URLs from the selected season, matches event names to explicit slugs, compares all driver classifications and awarded GP points, and stores downloaded HTML with SHA-256. Driver accents are normalized; the explicit Guanyu Zhou / Zhou Guanyu alias handles name ordering. Non-classified drivers retain their order excluding disqualified/non-starting entries. Constructor identity, birthdays and legal proceedings are not inferred from this table. Unsupported events, missing rows and identity discrepancies remain errors. A season check returns nonzero on any discrepancy/access failure and saves `baseline-YYYY.json`; already checked events are retained for recovery.

Agreement yields **matched**, not blanket confirmation. Formula1.com and Jolpica can share upstream timing data; agreement is not proof of independent historical coverage or closed appeals. The baseline is explicitly limited to the imported season(s).

## FIA documents

```bash
python3 -m f1tracker --data-dir /persistent/f1-data collect-fia 2024-24-gp https://www.fia.com/documents/championships/fia-formula-one-world-championship-14/season/season-2024-2043 --download-finals
```

The explicit season index may show the most recent GP. The collector accepts only PDF links matching the requested year/event. For another event, use its actual event-specific FIA index URL. Never guess a PDF path. `--download-finals` requires the system `pdftotext` command (Poppler); the cloud development machine already provides it. Other commands use the Python standard library only. Normal HTTPS checks remain enabled.

The collector stores a manifest of actual linked documents, archives final PDFs, validates year/event and the final classification title, extracts the document number, and compares the podium. It does **not** infer that protests, appeals or investigations are closed. Multiple final versions, later decisions and document publication dates must be reviewed. Event-specific FIA pages may return HTTP 403 even when the season index works; record the access gap and use lawfully obtained evidence for manual review. A final title or HTTP 200 alone never clears a pending case.

## Preserve explicit review conclusions

```bash
python3 -m f1tracker --data-dir /persistent/f1-data review-template 2024-24-gp decisions > /tmp/review.json
# Fill the template after inspecting the actual evidence, then:
python3 -m f1tracker --data-dir /persistent/f1-data review-import /tmp/review.json
```

The input is a list of review objects: event_id, capability, fingerprint, status, reviewer, checked_at, note, and evidence. Every evidence entry has its actual HTTPS URL, title, publisher, retrieval timestamp, and content SHA-256. The template deliberately contains no invented evidence or confirmation. `confirmed` is a reviewer assertion: validation cannot prove the research was performed. For `decisions`, confirmation additionally requires `official_status: final`, `open_cases: []`, and FIA evidence. Never clear cases solely because a document is old or titled final.

Capabilities are classification, points, constructors, birth_dates, grid, finish, and decisions. Supported statuses are matched (automatic source agreement), confirmed (explicit evidence review), blocked (unresolved conflict/case). An old fingerprint makes a review stale. Review dates and evidence retain the as-of time; no conclusion promises that future appeals are impossible. Recheck official documents regularly.

Claims require classification and decisions for every event in their comparison history, plus only their additional fields: constructor metrics need constructors, points metrics need points, age metrics need birth_dates, grid metrics need grid, and positions_gained also needs finish. This is a conservative full-history dependency for each metric, not a minimal per-driver dependency graph. Missing birthday evidence no longer blocks a separately verified win claim. Report status may be mixed, and each claim includes exact gaps and review IDs. A missing field can still disable computation of its metric under the original engine rules.

Reviews are stored separately from API snapshots. Ordinary resync retains confirmations; changed relevant facts invalidate them automatically. Reviews/old evidence are retained for audit and exported as JSON. Identical reviews with only new retrieval/check timestamps do not generate duplicate revisions. Imported review changes refresh existing reports; after an interrupted export, rerun export or the review import. A new contrary review supersedes the prior capability status while preserving its history.

## Remaining limits

This release automates result-table comparison, collects FIA evidence and persists explicit legal/historical review. It does not automatically interpret every steward decision or adjudicate appeals. Constructor lineage, biographies, full FIA proceedings and broader historical populations still require suitable evidence and review. Real reports remain provisional until their required reviews are complete. No external notification sender, scheduler or environment publication is enabled.
