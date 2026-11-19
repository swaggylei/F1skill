# Python tracker runtime

For the v0.2 evidence workflow, see [verification.md](verification.md). The core import/export commands below remain available.

The full repository contains an optional standard-library Python 3.10+ runtime for Linux/macOS. Work from the repository root; there is no package installation, build step, dependency lockfile or model API key. The portable instruction skill still works on other hosts. Each cloud task already has an isolated checkout; do not create a Git worktree unless requested.

## Commands and persistence

```bash
python3 -m f1tracker rules
python3 -m f1tracker --data-dir /tmp/f1skill-demo import examples/synthetic-season.json --backfill
python3 -m f1tracker --data-dir /tmp/f1skill-demo --language bilingual export
python3 -m f1tracker --data-dir /tmp/f1skill-demo status
python3 -m f1tracker --data-dir /tmp/f1skill-demo outbox
python3 -m f1tracker --data-dir /tmp/f1skill-demo backup /tmp/f1skill-demo-backup.sqlite3
```

`--data-dir` overrides `F1_KNOWLEDGE_DATA_DIR`; otherwise the default is `./f1-knowledge-data`. Use a new, empty directory for the synthetic demo. Never distribute synthetic reports as race news. The example's `example.org` URLs are deliberately non-evidentiary placeholders.

Files:

- `tracker.sqlite3`: authoritative events, report revisions, coverage, run outcomes and notification outbox. SQLite WAL and an OS writer lock prevent overlapping writes. All events/reports/outbox changes from one snapshot commit in one transaction.
- `events/<event-id>/rN.json`: normalized source snapshots, retained across corrections.
- `reports/<event-id>/rN.json` and `rN.zh.md` (or `.en.md` / `.bilingual.md`): bounded reports and source provenance. All six report sections are present; v0.1 has no arbitrary-curiosity generator for WEIRD & INTERESTING.
- `source-cache/<sha256>.json`: immutable downloaded API pages for audit. It is not a stale-data fallback. Fetch failures stay failures.

Exports use sibling temporary files and atomic replacement. If the process dies after the database commit, rerun `export` or the same import/sync: exports regenerate from SQLite without duplicate outbox entries. Runs interrupted before commit remain marked interrupted/failed and can be retried. A failed export can leave a successful discovery watermark because the database is already committed; check the latest run status and repair exports before delivery.

Use `backup` for a consistent SQLite copy, rather than copying an active database without its WAL. To restore, stop tracker processes, put the backup at `tracker.sqlite3` in a **new** data directory, then run `export`. Copy the source-cache separately if raw-response audit history is needed. Never overwrite a damaged original; preserve it for recovery. Database version mismatch/corruption causes an error, not a reset.

## Live data

```bash
python3 -m f1tracker --data-dir ./f1-knowledge-data sync --start-year 2023 --end-year 2024
```

The API endpoint is `https://api.jolpi.ca/ergast/f1/`. Add **api.jolpi.ca** to the environment's allowed destinations if blocked. Existing official-source domains are still needed for the wider skill's review. No token is required by the adapter. Normal TLS verification stays enabled. The earlier proxy 403 was resolved by publishing the allowed-domain configuration. Live 2024 season synchronization and an idempotent rerun subsequently passed.

The adapter reads a season calendar plus paginated GP results (100 items/page), merges races split across pages, checks totals and identities, and archives responses. It uses a versioned User-Agent, spaces requests by 0.3 seconds and retries transient errors at most three times with bounded backoff. Permanent 403 is not retried unchanged. Long server-requested cooldowns produce an operational error for the next run. See [Jolpica documentation](https://github.com/jolpica/jolpica-f1/blob/main/docs/README.md) and [rate limits](https://github.com/jolpica/jolpica-f1/blob/main/docs/rate_limits.md); adjust schedule to provider limits.

Each sync rechecks the entire selected range, including previously processed events. This is intentionally simple for a few seasons and catches retroactive results changes. Changing pagination totals, missing calendar events, duplicate drivers or a past scheduled GP without results stop the snapshot before any events commit. A missing result more than eight hours after scheduled start is flagged for investigation; it is never inferred to be completed, cancelled, or a successful no-op. Results, not scheduled start times, trigger import. Postponements/cancellations or renumbering may need explicit review; v0.1 does not silently rewrite event identities.

Initial execution builds a baseline from all input events and reports only the newest GP. `--backfill` explicitly reports all input events. Later new GPs are reported chronologically. Every update replays the imported scope to recompute affected metrics. Report revisions depend on semantic results, evidence and rule versions; merely retrieving identical data later does not create revisions. Changed historical evidence is included in downstream report provenance and may generate correction revisions even when a headline number is unchanged.

## Normalized input contract

`import PATH` accepts a complete JSON snapshot, not incremental partial rows. The full repository's `examples/synthetic-season.json` demonstrates the shape; this example is not bundled when only the portable skill folder is copied.

Top-level fields:

- `schema_version`: `1`.
- `coverage`: `label`, `start_season`, `end_season`, `expected_event_ids`. The expected list must match the actual event set. Supported years are 2000 onward; each represented season must include a continuous prefix starting at round 1. Use an explicit, honest coverage label. Keep the same start and label in one database; extending the end season is allowed. Existing events cannot disappear from a later snapshot.
- `events`: completed `gp` sessions with stable `YYYY-RR-gp` IDs, season, round, name, ISO race date, `completed: true`, `official_status` (`unknown`, `provisional`, `final`), `verification` (`provisional`, `confirmed`), `pending_reviews`, `sources`, and `results`.
- Each source: specific HTTPS `url`, `title`, `publisher`, `role` (`official`, `historical`, `secondary`), and timezone-aware `retrieved_at`. Reports include normalized snapshot SHA-256 fingerprints so source revisions are traceable. Metadata assertions alone do not verify a source.
- Each result: stable `driver_id`, `constructor_id`, `date_of_birth` (ISO date or null), `position` (official final rank or null), `grid` (actual positive starting grid or null), `points` (awarded GP points as a decimal string), `started`, `disqualified`, and `finished` (physically finished, or null if unknown). A classified non-finisher is not a physical finisher. Use null grid for pit lane/unknown; never turn it into P0. DSQ/non-starters have null rank, zero points and cannot be finishers. Duplicate drivers/shared drives are rejected.

Inputs are trusted declarations of the historical population. Validation checks consistency, not whether a caller omitted an unlisted final round or supplied false facts. The API adapter checks against the fetched calendar; independent official comparison remains necessary. No importer can derive missing evidence from a syntactically valid file.

For manual confirmation, review each event's official classification/decisions and historical comparator; set `official_status: final`, resolve `pending_reviews`, supply distinct official/historical evidence and `reviewed_by`, then set `verification: confirmed`. The software validates this declaration, not the human research. A claim stays provisional if any preceding event in its comparison scope is provisional. An appeal remains pending even if the document title says final. Legacy confirmation fields embedded inside imported API snapshots are not a persistent review workflow. In v0.2 use `review-import` to store evidence separately; ordinary API refresh preserves those reviews and relevant fact changes mark them stale.

## Twenty metric definitions (version 1)

Every value is **within the imported GP scope**, never automatically an all-time or full-career statistic. Counts start at the coverage boundary. The first in-scope benchmark has unknown before-value, not an invented zero. Missing history can truncate streaks and intervals. Equal maxima/minima retain joint holders; only strict improvement is a broken benchmark. Own-record extensions are labeled.

| Rule ID | Definition |
|---|---|
| driver_wins | Maximum GP wins per driver in scope |
| driver_podiums | Maximum top-three classifications per driver |
| driver_points | Maximum GP appearances with positive awarded points; not necessarily a physical finish |
| constructor_wins | Maximum wins per exact constructor ID |
| constructor_podiums | Maximum podium **places** per constructor, counted per car |
| driver_win_streak | Longest winning streak in calendar GP order |
| driver_podium_streak | Longest top-three streak in calendar GP order |
| driver_points_streak | Longest positive-points streak in calendar GP order |
| constructor_win_streak | Longest constructor winning streak in calendar GP order |
| youngest_winner / oldest_winner | Minimum / maximum winner age in calendar days |
| youngest_podium / oldest_podium | Minimum / maximum podium age in calendar days |
| win_gap_days | Maximum days between a driver's successive in-scope wins |
| podium_gap_days | Maximum days between successive in-scope podiums |
| positions_gained | Maximum positive actual-grid minus final-position difference among physical finishers |
| winning_grid | Highest numeric grid position of a winner |
| podium_grid | Highest numeric grid position of a podium finisher |
| podium_trio | Maximum occurrence count of an unordered set of three podium driver IDs |
| constructor_one_two | Maximum count of a constructor occupying P1 and P2 |

Absence/DNS/DSQ breaks a driver's calendar streak. Constructor aliases are not merged. Age uses declared race dates, not invented sub-day precision. GP points are not normalized across rule eras and Sprint points are excluded. Numeric grid rules exclude pit lane/unknown positions by disabling that metric's comparison once a relevant missing grid appears. Missing eligible birth dates disable the relevant age metric for this and subsequent comparisons. Missing finish information disables positions-gained comparisons. Disabled rules are shown in reports. Fix the source snapshot and replay to restore them.

No built-in automatic pole, fastest-lap, Sprint, career-start, pre-2000 shared-drive or arbitrary-combination discovery is claimed. The original skill can research those separately with evidence.

## Scheduling and delivery

No recurring service, external sender, or environment publication is created by these commands. After live validation, an existing persistent Linux host can schedule the CLI, for example once daily:

```cron
15 3 * * * cd /path/to/F1skill && python3 -m f1tracker --data-dir /persistent/f1-data sync --start-year 2023 --end-year 2026 >> /persistent/f1-sync.log 2>&1
```

Set the path, season range, host timezone and log rotation explicitly. During race weekends a higher frequency can be used within provider limits. A cloud snapshot does not retain a running scheduler process. An ephemeral CI runner needs explicitly durable storage and concurrency control; do not put its only SQLite copy on a disposable runner filesystem.

Exit `0` means execution completed; no changes produce empty stdout. Exit `1` and stderr mean failure; forward those to the host's operational error channel. `status` reports the latest run, pending event reviews and local notification count. A successful no-op updates the run log; no external user notice is required.

`outbox` returns pending stable notification IDs. A superseded undelivered revision is removed from the pending list; previously acknowledged revisions retain their history. An authorized external sender can use the ID as an idempotency key, fetch the matching report, and run `ack ID` **only after confirmed delivery**. The CLI itself sends nothing. Exactly-once external delivery requires receiver-side idempotency or reconciliation after a crash; marking a notification acknowledged is not proof it was delivered. Review the provisional status before choosing an automatic distribution policy.

## Validation and release limits

```bash
python3 -m unittest discover -s tests -v
```

Synthetic tests cover all twenty metric IDs and documented persistence/failure cases. A small factual fixture from the Formula1.com 2024 Bahrain/Saudi Arabian classifications and grids checks selected calculations; birth dates and FIA decisions are deliberately not inferred. It uses today's historical pages, not archived as-issued decisions. Before unattended factual reporting, restore a backup in a new directory, validate API access and complete season coverage, compare additional real races with official sources, and observe several actual race weekends including revisions. Broader automatic interpretation of FIA decisions, alert integration and broader historical data coverage are subsequent work.
