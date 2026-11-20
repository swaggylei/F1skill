"""Export a bounded GP snapshot or a tracker database into an offline website."""
import argparse
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from f1tracker.model import validate
from f1tracker.rules import RULES, evaluate


def load(path):
    if path.suffix != ".sqlite3":
        return json.loads(path.read_text(encoding="utf-8"))
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
        coverage = json.loads(db.execute("SELECT value FROM meta WHERE key='coverage'").fetchone()[0])
        events = [json.loads(row[0]) for row in db.execute(
            "SELECT payload FROM event_versions e WHERE revision = "
            "(SELECT MAX(revision) FROM event_versions WHERE event_id=e.event_id)")]
    return {"schema_version": 1, "events": events, "coverage": coverage}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, nargs="?", default=ROOT / "tests/fixtures/2024-opening.json")
    args = parser.parse_args()
    snapshot = load(args.source)
    data = validate(snapshot)
    events = data["events"]
    # Publish observations as provisional until a separate web publication review.
    for event, report in zip(events, evaluate(events, data["coverage"])):
        event["claims"] = [{key: c[key] for key in ("rule_id", "category", "entities", "before", "after", "tied", "unit")}
                           for c in report["claims"]]
        event["disabled_rules"] = report["disabled_rules"]
    data["rules"] = RULES
    target = Path(__file__).parent / "dist/data.js"
    target.write_text("window.PITWALL = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n",
                      encoding="utf-8")
    print(f"Exported {len(events)} GPs to {target.name}")


if __name__ == "__main__":
    main()
