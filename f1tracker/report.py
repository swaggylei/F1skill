"""Portable JSON and Markdown views; no external delivery."""
from .rules import RULES

SECTIONS = ("NEW RECORDS", "BROKEN RECORDS", "ENDED STREAKS", "WEIRD & INTERESTING", "STILL ACTIVE", "HISTORICAL CONTEXT")


def safe(value):
    return str(value).replace("\n", " ").replace("<", "&lt;").replace(">", "&gt;").replace("[", "\\[").replace("]", "\\]")


def render(report, language="zh"):
    def words(zh, en):
        return zh if language == "zh" else en if language == "en" else f"{zh} / {en}"
    coverage = report["coverage"]
    lines = [f'# {safe(report["name"])} — {report["event_id"]}', "",
             f'Revision: {report["revision"]} | {report["kind"]} | {report["verification"].upper()}',
             f'GP date: {report["date"]} | Official document status: {report["official_status"]}',
             f'Generated: {report.get("created_at", "unknown")} | Evidence cutoff: ' +
             max(s["retrieved_at"] for e in report["evidence"] for s in e["sources"]),
             words(f'范围：{safe(coverage["label"])}；{coverage["from"]} 至 {coverage["through"]}，{coverage["event_count"]} 场 GP。',
                   f'Scope: {safe(coverage["label"])}; {coverage["from"]} through {coverage["through"]}, {coverage["event_count"]} GPs.'),
             words('所有纪录仅限已导入范围，不代表生涯或历史最高；连续纪录可能在范围起点被截断。',
                   'All benchmarks are restricted to imported history, not career/all-time records; streaks may be left-censored.'), ""]
    for section in SECTIONS:
        lines.extend([f"## {section}", ""])
        claims = [c for c in report["claims"] if c["category"] == section]
        if section == "HISTORICAL CONTEXT":
            lines.append(words('按赛事日期和日历顺序计算；缺席中断连续纪录；GP 与 Sprint 分开。Constructor ID 不合并更名沿革。',
                               'Ordered by GP date/calendar; absence breaks streaks; Sprint excluded. Constructor IDs are not merged across renames.'))
        elif not claims:
            lines.append(words('无已核实变化；待复核项见下方。', 'No verified change; see pending reviews below.'))
        for c in claims:
            rule = RULES[c["rule_id"]]
            before = c["before"] if c["before"] is not None else words("未知／无范围内基准", "unknown / no in-scope benchmark")
            flags = []
            if c["tied"]:
                flags.append(words("并列", "tied/joint"))
            if c["self_extension"]:
                flags.append(words("延伸自身纪录", "extends own benchmark"))
            flags.append(c["verification"])
            lines.append(f'- {words(rule["zh"], rule["en"])} — {safe(", ".join(c["entities"]))}: '
                         f'{before} → {c["after"]} {c["unit"]} ({", ".join(flags)}). '
                         f'Previous holders: {safe(", ".join(c["previous_holders"])) or "—"}. ID: `{c["claim_id"]}`')
            gaps = c.get('verification_gaps', [])
            if gaps:
                reasons = sorted({g['capability'] + ': ' + g['reason'] for g in gaps})
                lines.append('  ' + words('待复核原因：', 'Review gaps: ') + safe('; '.join(reasons)))
            if c.get('review_ids'):
                lines.append('  Evidence reviews: ' + ', '.join(c['review_ids']))
        lines.append("")
    lines.extend(["## Coverage gaps / Pending reviews", "",
                  "Disabled rules: " + (", ".join(report["disabled_rules"]) or "none"),
                  "Pending events: " + (", ".join(report["pending_reviews"]) or "none"), "",
                  words('缺失年龄、发车位或完赛信息会禁用相关纪录的历史比较，不会按零处理。',
                        'Missing birth dates, grids or finish status disable affected historical comparisons; missing is not zero.'), "",
                  "## Evidence", ""])
    for evidence in report["evidence"]:
        lines.append(f'- {evidence["event_id"]} snapshot SHA-256: `{evidence["fingerprint"]}`')
        for source in evidence["sources"]:
            lines.append(f'- {evidence["event_id"]}: {safe(source["publisher"])} — {safe(source["title"])}; '
                         f'{source["url"]}; retrieved {source["retrieved_at"]}')
        for pending in evidence["pending_reviews"]:
            lines.append(f'  - Pending: {safe(pending)}')
    for review_id, review in report.get('review_evidence', {}).items():
        lines.append(f'- Review `{review_id}`: {safe(review["reviewer"])}; {review["checked_at"]}; {safe(review["note"])}')
        for source in review['evidence']:
            lines.append(f'  - {source["url"]}; SHA-256 `{source["sha256"]}`')
    return "\n".join(lines) + "\n"
