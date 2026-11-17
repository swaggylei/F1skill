---
name: f1-knowledge
description: Explore Formula 1 history, drivers and constructors, verify unusual statistics, and track post-Grand Prix records with sourced, persistent reports. Supports Chinese and English.
---

# F1 Knowledge / F1 知识

Provide evidence-led F1 knowledge with particular attention to surprising records. Work with any host that can read Markdown, browse reliable sources and persist files. Do not assume a particular plugin, API, scheduler or model.

## Modes / 工作模式

- **Knowledge / 知识**: answer questions about history, drivers, constructors, eras and unusual records. Read [knowledge.md](references/knowledge.md). Date current claims and distinguish fact, interpretation and folklore.
- **Track / 追踪**: on each invocation, look for completed Grand Prix weekends since the previous run and process them chronologically. Read [tracking.md](references/tracking.md), [definitions.md](references/definitions.md), [sources.md](references/sources.md), and [state.md](references/state.md).
- **Audit / 复核**: recheck provisional claims and official revisions, recompute affected downstream records, preserve correction history.

Infer mode from the request. Default reports to concise Chinese with English proper names and the six English section labels. If English is requested, write the equivalent English report; if bilingual is requested, pair Chinese and English per claim. Knowledge answers follow the user's language.

## Evidence invariants / 核验底线

Use the latest available FIA final classification, official qualifying results and Formula1.com material. Cross-check historical claims against reliable historical statistics. Cite specific documents/pages, retrieval dates and coverage, not just homepages. Browse for current facts; never infer completion from a scheduled start time.

Keep Grand Prix, Sprint, qualifying, grid position, pole credit and fastest-lap statistics separate unless an explicit record definition combines them. Define population, period, identity rules, units and tie handling before computing. A streak ending is not a historical record being beaten. A tie is not an outright record. Never turn an interesting observation into an unsupported all-time superlative.

Treat unsettled penalties, appeals and revisions as **provisional**, even when a document is titled final. Preserve official document status separately from claim verification status. Recheck pending items on every later run. Unknown history means a bounded claim or verification gap, never invented certainty.

Do not notify on routine no-new-GP runs. A material correction to an earlier report may produce a clearly labeled correction notice. A source-access failure must not be reported as “no new race”; expose it through the host's error/status channel, or a brief failure response if none exists. Save reports and state locally; external distribution requires host/user authorization.

The skill runs only when invoked. Recurring execution and quiet notification delivery require a host scheduler. Never claim background monitoring has been enabled merely by installing this skill.
