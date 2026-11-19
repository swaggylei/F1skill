# Portable persistence / 可迁移状态

Keep runtime data outside the installed skill. Use UTF-8 JSON and Markdown, UTC ISO-8601 timestamps and stable IDs; no API keys in state. Migrate the whole data folder across hosts. Git-ignore personal runtime data by default.

The optional Python v0.1 tracker uses `tracker.sqlite3` as its transactional source of truth, with revisioned JSON/Markdown exports. Its database is separate from the manual workflow's suggested `state.json`; it never silently imports or resets an existing manual state file. See [runtime.md](runtime.md) for backup, export recovery and scope limitations. When switching from an existing manual workflow, reconcile previously delivered reports before forwarding tracker outbox entries.

Suggested layout:

```text
f1-knowledge-data/
  state.json
  events/<event-id>/<revision>.json
  reports/<event-id>/<revision>.md
  runs/<run-id>.json
```

Minimum `state.json` structure (null means unknown, not zero):

```json
{
  "schema_version": 1,
  "last_attempt_at": null,
  "last_successful_check_at": null,
  "baseline": {"as_of": null, "first_covered_event": null, "coverage": []},
  "events": {},
  "claims": {},
  "pending_reviews": [],
  "pending_events": [],
  "delivery_log": []
}
```

Use event IDs from season plus official round and verified event identity; retain aliases if a calendar revision changes round numbers. Session IDs append `gp`, `sprint`, `qualifying` or `sprint-qualifying`. Do not use translated names alone as keys.

Each event stores actual end time, session results/provenance, evidence fingerprint, official document status, latest processed revision, report path and unresolved issues. Each claim stores `claim_id`, metric definition/version, session, population, period, entity IDs, units, before/after values, previous holders, ties, category, verification status (`confirmed`, `provisional`, `unverified`, `retracted`), sources, coverage, first reported event and revision history. A claim identity derives from definition + scope + entity + event; changing evidence changes its revision, not identity. Distinct events that legitimately extend a record remain distinct changes.

`pending_reviews` holds reason, affected event/claims, last checked time and next review condition. Recheck at every invocation while unresolved; official final documents still need revision checks for recently reported events and any known open proceedings. On resolution recompute later affected totals/streaks, update status, and issue one material correction. Never erase the old evidence trail.

Each run logs discovery coverage, candidate checks, gaps, event successes/failures and no-op reason. `last_successful_check_at` advances only after a complete discovery check; per-event backlog is retained separately. Never use that timestamp as the sole discovery filter.

Delivery is separate from report creation: use a stable event/revision notification ID with the host's idempotency mechanism if available. Mark delivered only after confirmation; otherwise mark delivery unknown and reconcile before retrying. Exactly-once external delivery cannot be promised without host support. Routine no-new-GP runs save a run log and produce no user notification. Corrections and operational failures follow SKILL.md's explicit exceptions.

Atomic write: write a sibling temporary file, flush and replace on the same filesystem under a lock. Keep a recoverable previous state. On invalid state/schema, preserve it and recover from reports/evidence or request the missing baseline; never silently reset and resend old reports.
