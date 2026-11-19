"""Twenty versioned metrics. Every benchmark is bounded by the imported history."""
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal

from .model import digest, semantic
from .verification import claim_review

VERSION = "1"
# ID, Chinese title, English title, unit, direction, computation type
SPECS = [
    ("driver_wins", "车手胜场", "Driver GP wins", "count", "max", "total"),
    ("driver_podiums", "车手领奖台次数", "Driver GP podiums", "count", "max", "total"),
    ("driver_points", "车手获积分场次", "Driver GP points-scoring appearances", "count", "max", "total"),
    ("constructor_wins", "Constructor 胜场", "Constructor GP wins", "count", "max", "total"),
    ("constructor_podiums", "Constructor 领奖台席位数", "Constructor GP podium places", "count", "max", "total"),
    ("driver_win_streak", "车手连续获胜", "Consecutive GP wins", "races", "max", "streak"),
    ("driver_podium_streak", "车手连续领奖台", "Consecutive GP podiums", "races", "max", "streak"),
    ("driver_points_streak", "车手连续获积分", "Consecutive GP points scores", "races", "max", "streak"),
    ("constructor_win_streak", "Constructor 连续获胜", "Consecutive constructor GP wins", "races", "max", "streak"),
    ("youngest_winner", "最年轻获胜年龄", "Youngest GP winner age", "days", "min", "value"),
    ("oldest_winner", "最年长获胜年龄", "Oldest GP winner age", "days", "max", "value"),
    ("youngest_podium", "最年轻领奖台年龄", "Youngest GP podium age", "days", "min", "value"),
    ("oldest_podium", "最年长领奖台年龄", "Oldest GP podium age", "days", "max", "value"),
    ("win_gap_days", "两次获胜间隔", "Days between successive GP wins", "days", "max", "gap"),
    ("podium_gap_days", "两次领奖台间隔", "Days between successive GP podiums", "days", "max", "gap"),
    ("positions_gained", "完赛名次提升", "Positions gained by a finisher", "places", "max", "value"),
    ("winning_grid", "获胜者最靠后发车位", "Lowest numeric winning grid position", "position", "max", "value"),
    ("podium_grid", "领奖台车手最靠后发车位", "Lowest numeric podium grid position", "position", "max", "value"),
    ("podium_trio", "相同领奖台三人组合次数", "Unordered podium trio occurrences", "count", "max", "total"),
    ("constructor_one_two", "Constructor 包揽前二次数", "Constructor one-two occurrences", "count", "max", "total"),
]
RULES = {row[0]: dict(zip(("id", "zh", "en", "unit", "direction", "kind"), row), version=VERSION) for row in SPECS}


def evaluate(events, coverage):
    totals, streaks, last_dates = defaultdict(Counter), defaultdict(Counter), defaultdict(dict)
    best = {}
    gaps = set()
    evidence = []
    historical_provisional = False
    for index, event in enumerate(events):
        evidence.append({"event_id": event["event_id"], "fingerprint": digest(semantic(event)), "sources": event["sources"],
                         "official_status": event["official_status"], "pending_reviews": event["pending_reviews"]})
        historical_provisional |= event["verification"] != "confirmed"
        verification = "provisional" if historical_provisional else "confirmed"
        observed = defaultdict(Counter)
        day = date.fromisoformat(event["date"])
        podium = sorted((r for r in event["results"] if r["position"] in (1, 2, 3)), key=lambda r: r["position"])
        for row in event["results"]:
            driver, team = row["driver_id"], row["constructor_id"]
            pos = row["position"]
            winner = pos == 1
            on_podium = pos in (1, 2, 3)
            scoring = Decimal(row["points"]) > 0
            for metric, eligible, entity in [
                ("driver_wins", winner, driver), ("driver_podiums", on_podium, driver),
                ("driver_points", scoring, driver), ("constructor_wins", winner, team),
                ("constructor_podiums", on_podium, team), ("driver_win_streak", winner, driver),
                ("driver_podium_streak", on_podium, driver), ("driver_points_streak", scoring, driver),
                ("constructor_win_streak", winner, team),
            ]:
                if eligible:
                    observed[metric][entity] += 1
            for kind, eligible in (("winner", winner), ("podium", on_podium)):
                if eligible:
                    if row["date_of_birth"] is None:
                        gaps.update((f"youngest_{kind}", f"oldest_{kind}"))
                    else:
                        age = (day - date.fromisoformat(row["date_of_birth"])).days
                        observed[f"youngest_{kind}"][driver] = age
                        observed[f"oldest_{kind}"][driver] = age
            for metric, eligible in (("win_gap_days", winner), ("podium_gap_days", on_podium)):
                if eligible:
                    if driver in last_dates[metric]:
                        observed[metric][driver] = (day - last_dates[metric][driver]).days
                    last_dates[metric][driver] = day
            for metric, eligible in (("winning_grid", winner), ("podium_grid", on_podium)):
                if eligible:
                    if row["grid"] is None:
                        gaps.add(metric)
                    else:
                        observed[metric][driver] = row["grid"]
            if row["started"] and not row["disqualified"]:
                if row["finished"] is None:
                    gaps.add("positions_gained")
                elif row["finished"]:
                    if row["grid"] is None or pos is None:
                        gaps.add("positions_gained")
                    elif row["grid"] > pos:
                        observed["positions_gained"][driver] = row["grid"] - pos
        trio = "+".join(sorted(r["driver_id"] for r in podium))
        observed["podium_trio"][trio] = 1
        if podium[0]["constructor_id"] == podium[1]["constructor_id"]:
            observed["constructor_one_two"][podium[0]["constructor_id"]] = 1
        claims, active = [], []

        def claim(metric, entities, before, after, category, tied=False, previous_holders=None):
            # Scope end grows; identity remains tied to the fixed start and definition.
            identity = [coverage["start_season"], event["event_id"], metric, VERSION, category, sorted(entities)]
            return {"claim_id": digest(identity)[:24], "rule_id": metric, "rule_version": VERSION,
                    "session": "gp", "entities": sorted(entities), "before": before, "after": after,
                    "previous_holders": sorted(previous_holders or []), "tied": tied,
                    "self_extension": category == "BROKEN RECORDS" and bool(set(entities) & set(previous_holders or [])),
                    "unit": RULES[metric]["unit"], "category": category,
                    **claim_review(metric, events[:index + 1])}

        for metric, spec in RULES.items():
            values = dict(observed[metric])
            if spec["kind"] == "total":
                totals[metric].update(values)
                values = {entity: totals[metric][entity] for entity in values}
            elif spec["kind"] == "streak":
                for entity in sorted(set(streaks[metric]) | set(values)):
                    previous = streaks[metric][entity]
                    if entity in values:
                        streaks[metric][entity] = previous + 1
                    else:
                        streaks[metric][entity] = 0
                        if previous >= 2:
                            claims.append(claim(metric, [entity], previous, 0, "ENDED STREAKS"))
                values = {entity: streaks[metric][entity] for entity in values}
                active.extend(claim(metric, [entity], None, value, "STILL ACTIVE")
                              for entity, value in sorted(values.items()) if value >= 2)
            if metric in gaps or not values:
                continue
            optimum = (min if spec["direction"] == "min" else max)(values.values())
            entities = sorted(k for k, v in values.items() if v == optimum)
            old = best.get(metric)
            better = old is None or (optimum < old[0] if spec["direction"] == "min" else optimum > old[0])
            if better:
                claims.append(claim(metric, entities, old[0] if old else None, optimum,
                                    "BROKEN RECORDS" if old else "NEW RECORDS", len(entities) > 1,
                                    old[1] if old else []))
                best[metric] = (optimum, entities)
            elif optimum == old[0]:
                # Repeated individual performances count as ties, never broken records.
                claims.append(claim(metric, entities, old[0], optimum, "NEW RECORDS", True, old[1]))
                best[metric] = (optimum, sorted(set(old[1]) | set(entities)))
        claimed = {(c["rule_id"], entity) for c in claims for entity in c["entities"]}
        claims.extend(c for c in active if not any((c["rule_id"], e) in claimed for e in c["entities"]))
        states = {c['verification'] for c in claims}
        verification = next(iter(states)) if len(states) == 1 else 'mixed' if states else 'provisional'
        yield {"schema_version": 1, "engine_version": VERSION, "event_id": event["event_id"],
               "name": event["name"], "date": event["date"], "session": "gp",
               "official_status": event["official_status"], "verification": verification,
               "coverage": {"label": coverage["label"], "from": events[0]["date"], "through": event["date"],
                            "event_count": index + 1, "scope": "declared imported GP history; not all-time or career totals"},
               "claims": claims, "disabled_rules": sorted(gaps), "evidence": list(evidence),
               "pending_reviews": sorted({g['event_id'] for c in claims for g in c['verification_gaps']}),
               "review_evidence": {r['review_id']: r for e in events[:index + 1] for r in e.get('_reviews', {}).values()}}
