"""Validate complete, normalized GP snapshots before touching persistent state."""
import copy
import hashlib
import json
import re
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit


class DataError(ValueError):
    pass


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def semantic(value):
    """Retrieval time is provenance, not a new race result."""
    if isinstance(value, dict):
        return {k: semantic(v) for k, v in value.items() if k != "retrieved_at"}
    if isinstance(value, list):
        return [semantic(v) for v in value]
    return value


def require(condition, message):
    if not condition:
        raise DataError(message)


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,100}", value), "Invalid stable ID")


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, "Timestamp must include timezone")
    return parsed


def validate(snapshot):
    """Return a canonical copy; reject gaps, duplicates and unsupported sessions."""
    try:
        data = copy.deepcopy(snapshot)
        require(data["schema_version"] == 1, "Unsupported input schema_version")
        coverage = data["coverage"]
        require(isinstance(coverage["label"], str) and coverage["label"].strip(), "Coverage label required")
        start, end = coverage["start_season"], coverage["end_season"]
        require(type(start) is int and type(end) is int and 2000 <= start <= end <= date.today().year,
                "v1 supports explicit seasons from 2000 through the current year")
        events = sorted(data["events"], key=lambda e: (e["season"], e["round"]))
        require(events, "No completed GP results; this is not a successful no-op")
        ids = [e["event_id"] for e in events]
        expected = coverage["expected_event_ids"]
        require(len(ids) == len(set(ids)) and len(expected) == len(set(expected)), "Duplicate event IDs")
        require(set(ids) == set(expected), "Coverage gap: expected GP IDs and results differ")
        previous_date = None
        drivers = {}
        for season in range(start, end + 1):
            rounds = [e["round"] for e in events if e["season"] == season]
            require(rounds and rounds == list(range(1, max(rounds) + 1)),
                    f"Missing or unordered rounds in {season}; v1 requires an uninterrupted season prefix")
        for event in events:
            identifier(event["event_id"])
            require(event["session"] == "gp", "Only GP sessions are supported; never import Sprint as GP")
            require(event["completed"] is True, "Scheduled time does not prove completion")
            require(start <= event["season"] <= end and type(event["round"]) is int, "Event outside coverage")
            require(event["event_id"] == f'{event["season"]}-{event["round"]:02d}-gp', "Event ID/season/round mismatch")
            day = date.fromisoformat(event["date"])
            require(day.year == event["season"] and day <= date.today(), "Invalid event date")
            require(previous_date is None or day > previous_date, "Events must be in chronological order")
            previous_date = day
            require(isinstance(event["name"], str) and event["name"], "Event name required")
            require(event["official_status"] in ("unknown", "provisional", "final"), "Invalid official status")
            require(event["verification"] in ("provisional", "confirmed"), "Invalid verification status")
            require(isinstance(event["pending_reviews"], list), "pending_reviews must be a list")
            require(event["sources"], "Specific source provenance required")
            for source in event["sources"]:
                url = urlsplit(source["url"])
                require(url.scheme == "https" and url.hostname and not url.username and not url.password,
                        "Source must be an HTTPS URL without credentials")
                require(source["title"] and source["publisher"], "Source title and publisher required")
                require(source["role"] in ("official", "historical", "secondary"), "Invalid source role")
                timestamp(source["retrieved_at"])
            if event["verification"] == "confirmed":
                require(event.get("reviewed_by") and not event["pending_reviews"] and event["official_status"] == "final",
                        "Confirmation requires a named reviewer, final status and no unresolved reviews")
                require({"official", "historical"} <= {s["role"] for s in event["sources"]},
                        "Confirmation requires official and historical evidence reviewed by a human")
            rows = event["results"]
            require(len(rows) >= 3, "Incomplete classification")
            seen, positions, grids = set(), set(), set()
            for row in rows:
                for field in ("driver_id", "constructor_id"):
                    identifier(row[field])
                driver = row["driver_id"]
                require(driver not in seen, "Duplicate driver / shared drives unsupported in v1")
                seen.add(driver)
                require(type(row["started"]) is bool and type(row["disqualified"]) is bool, "Explicit start/DSQ flags required")
                require(row["finished"] is None or type(row["finished"]) is bool, "Invalid finished flag")
                points = Decimal(str(row["points"]))
                require(points.is_finite() and points >= 0, "Invalid awarded GP points")
                row["points"] = str(points.normalize())
                pos = row["position"]
                if row["disqualified"] or not row["started"]:
                    require(pos is None and points == 0 and row["finished"] is not True,
                            "DSQ/non-starter cannot have a classification, points or finish")
                elif pos is not None:
                    require(type(pos) is int and pos > 0 and pos not in positions, "Duplicate/invalid classification position")
                    positions.add(pos)
                grid = row["grid"]
                require(grid is None or (type(grid) is int and grid > 0 and grid not in grids),
                        "Grid must be positive and unique; pit lane/unknown = null")
                if grid is not None:
                    grids.add(grid)
                dob = row["date_of_birth"]
                if dob is not None:
                    require(date.fromisoformat(dob) < day, "Invalid date of birth")
                require(driver not in drivers or drivers[driver] == dob, "Inconsistent driver birth dates")
                drivers[driver] = dob
            require({1, 2, 3} <= positions, "Top-three classification is incomplete")
            event["results"] = sorted(rows, key=lambda r: r["driver_id"])
            event["sources"] = sorted(event["sources"], key=lambda s: (s["url"], s["role"]))
        data["events"] = events
        coverage["expected_event_ids"] = ids
        return data
    except (KeyError, TypeError, InvalidOperation, OverflowError) as exc:
        raise DataError(f"Malformed snapshot: {exc}") from exc
