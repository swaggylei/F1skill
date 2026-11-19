# Tracking workflow / 赛后追踪流程

For deterministic v0.1 execution, use [runtime.md](runtime.md). That implementation supports a documented subset of GP-only discovery families below; keep wider agent research and official evidence review explicit.

1. Resolve a writable data directory (`F1_KNOWLEDGE_DATA_DIR` if configured, otherwise `./f1-knowledge-data`). Read state and previous reports. Capture UTC run start and user display timezone. Prevent concurrent writers with a host lock; if unavailable, stop overlapping updates.
2. On first run, initialize an explicitly dated baseline and process the most recently completed GP weekend. Do not label all historical facts as new. Older catch-up requires an explicit start date. Record the earliest covered event and historical data coverage. An empty baseline cannot establish a before-value without historical evidence.
3. Discover actual completed GPs from official results and calendar, across season boundaries. Compare stable event IDs and processed revisions, not only a timestamp. Recheck unresolved events and unfinished backlog even if last run was recent. A postponed/cancelled event is not a completed GP. A completed Sprint alone does not trigger the weekend report; include it when that weekend's GP has ended. A cancelled GP may be logged as an exceptional event but must not count as a GP start/result.
4. Obtain the latest FIA race classification, qualifying classification, applicable stewards decisions, official Sprint classification when applicable, and fastest-lap evidence. Confirm year/session/event on every document: an official landing page may default to another season. Save document numbers, issued times and retrieval times. Verify Formula1.com and historical cross-checks. If blocked, preserve backlog, mark gaps and do not advance the event to successfully processed.
5. Reconstruct the state immediately before each event. Compute changes session by session using definitions.md. For multiple unprocessed events, never compare every event with today's aggregate total. Record historical coverage and unknown fields explicitly.
6. Actively generate candidates across every discovery family below. Verify candidates against full relevant history or narrow their scope. Do not promise exhaustive discovery of all conceivable records. Save rejected/uncertain candidates with reasons, rather than publishing speculation.
7. Compare claim identities and evidence revisions against stored history. Publish one report per newly completed weekend, including an honest “no verified changes found” result when appropriate. Do not send a routine STILL ACTIVE-only update for an already reported event. A revised fact is a correction, not a new discovery disguised as a record.
8. Save report and evidence first, then update state using an atomic replacement. Retain old report revisions. On partial failure, commit only completed events and leave the remainder pending. A crash before state commit must be recoverable by checking report IDs; reruns must not duplicate notices.

## Discovery families / 主动挖掘

- Extremes: age, starts before first success, grid-to-result gain, classified finish gap; compare like-for-like units.
- Rankings: milestone counts, tied ranks, distinct winners/podium finishers; declare competition/dense ranking.
- Streaks: wins, points, finishes, poles, laps led; calendar consecutive vs consecutive participant starts, same venue vs same event name.
- Combinations: podium trios, nationality combinations, constructor doubles, pole-win-fastest lap; ensure every component is supported.
- Intervals: elapsed calendar days, intervening GP starts, seasons between wins/podiums; state endpoints and inclusion rules.
- Inversions: wins without pole, champions without a category lead, teammate contrasts; require denominators and avoid causal claims.
- Historical curiosities: shared drives, unusual classifications, rule-era effects, venue/name changes and returns. Verify anecdotes rather than repeating folklore.

Prefer a few strong discoveries over a quota. An exploratory combination may be described as an observation; “first ever” requires complete search coverage. Avoid arbitrary filters chosen only to manufacture uniqueness.

## Report contract / 报告格式

Header: event ID/name/year, GP completion time, report date/timezone, revision, evidence cutoff, FINAL / PROVISIONAL / MIXED, data coverage.

Use all six sections; an empty section says “无已核实变化 / No verified change”:

1. **NEW RECORDS** — a first occurrence or newly established defined benchmark; mark tied records explicitly.
2. **BROKEN RECORDS** — an existing historical benchmark surpassed; name the previous holder and benchmark. Own-record extensions belong here and must say “延伸自身纪录”.
3. **ENDED STREAKS** — an actual sequence ended; retain any historical best that still stands.
4. **WEIRD & INTERESTING** — verified curiosities, with scoped claims when history is incomplete.
5. **STILL ACTIVE** — relevant active streaks and proximity to benchmarks; avoid recycled filler and predictions presented as facts.
6. **HISTORICAL CONTEXT** — short era/rules/identity comparisons necessary to interpret the above.

Each claim: stable ID; definition and session; population/time range; driver/constructor; before → after (including previous holders, ties and units); status; why interesting; direct source links and access date; historical coverage/gaps. If a field is unknown write unknown, not zero. Put verification gaps and pending review at the end. Avoid duplicating a single claim in multiple sections; cross-reference its ID instead.
