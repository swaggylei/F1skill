import copy
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
from datetime import datetime, timezone

from f1tracker.__main__ import main
from f1tracker.model import DataError, validate
from f1tracker.report import render
from f1tracker.rules import RULES, evaluate
from f1tracker.source import Client, normalize, pages, sync
from f1tracker.store import Store


def fixture(winners=("a", "a", "b", "a")):
    events = []
    for round_, winner in enumerate(winners, 1):
        order = [winner] + [d for d in "abcd" if d != winner]
        rows = [{"driver_id": d, "constructor_id": "red" if d in "ab" else "blue",
                 "date_of_birth": {"a": "1990-01-01", "b": "1995-01-01", "c": "1985-01-01", "d": "2000-01-01"}[d],
                 "position": p, "grid": {"a": 4, "b": 3, "c": 2, "d": 1}[d],
                 "points": str([25, 18, 15, 0][p - 1]), "started": True, "disqualified": False, "finished": True}
                for p, d in enumerate(order, 1)]
        events.append({"event_id": f"2024-{round_:02d}-gp", "season": 2024, "round": round_, "session": "gp",
                       "name": f"SYNTHETIC TEST GP {round_}", "date": f"2024-03-{round_ * 7:02d}", "completed": True,
                       "official_status": "unknown", "verification": "provisional", "pending_reviews": ["Synthetic test data"],
                       "sources": [{"url": f"https://example.org/synthetic/gp/{round_}", "title": "Synthetic fixture — not real race evidence",
                                    "publisher": "Test only", "role": "secondary", "retrieved_at": "2024-04-01T00:00:00Z"}],
                       "results": rows})
    return {"schema_version": 1, "coverage": {"label": "SYNTHETIC TEST — NOT REAL RACES", "start_season": 2024, "end_season": 2024,
                                               "expected_event_ids": [e["event_id"] for e in events]}, "events": events}


def reports(data):
    data = validate(data)
    return list(evaluate(data["events"], data["coverage"]))


def claim(report, rule):
    return next(c for c in report["claims"] if c["rule_id"] == rule)


class RulesTests(unittest.TestCase):
    def test_real_2024_opening_races_replay(self):
        data = json.loads((Path(__file__).parent / "fixtures/2024-opening.json").read_text())
        first, second = reports(data)
        self.assertEqual(claim(first, "positions_gained")["entities"], ["zhou_guanyu"])
        self.assertEqual(claim(first, "positions_gained")["after"], 6)
        self.assertEqual(claim(second, "driver_wins")["entities"], ["max_verstappen"])
        self.assertEqual(claim(second, "driver_wins")["after"], 2)
        self.assertEqual(claim(second, "constructor_podiums")["after"], 4)
        self.assertEqual(claim(second, "constructor_one_two")["after"], 2)
        self.assertEqual(claim(second, "win_gap_days")["after"], 7)
        self.assertEqual(second["verification"], "provisional")
        self.assertEqual(set(second["disabled_rules"]), {"youngest_winner", "oldest_winner", "youngest_podium", "oldest_podium"})

    def test_all_twenty_rules_exercised(self):
        result = reports(fixture())
        actual = {c["rule_id"] for r in result for c in r["claims"]}
        self.assertEqual(len(RULES), 20)
        self.assertEqual(actual, set(RULES))

    def test_known_counts_streaks_ages_gaps_and_grid(self):
        first, second, third, fourth = reports(fixture())
        expected = {
            "driver_wins": 3, "driver_podiums": 4, "driver_points": 4,
            "constructor_wins": 4, "constructor_podiums": 8,
            "driver_podium_streak": 4, "driver_points_streak": 4,
            "constructor_win_streak": 4, "win_gap_days": 14,
            "podium_gap_days": 7, "positions_gained": 3, "winning_grid": 4,
            "podium_grid": 4, "podium_trio": 4, "constructor_one_two": 4,
            "oldest_winner": (datetime(2024, 3, 28) - datetime(1990, 1, 1)).days,
            "oldest_podium": (datetime(2024, 3, 28) - datetime(1985, 1, 1)).days,
        }
        for rule, value in expected.items():
            self.assertEqual(claim(fourth, rule)["after"], value, rule)
        self.assertEqual(claim(first, "youngest_winner")["after"], 12484)
        self.assertEqual(claim(first, "youngest_podium")["after"], 10658)
        self.assertEqual(claim(second, "driver_win_streak")["after"], 2)
        self.assertTrue(claim(second, "driver_wins")["self_extension"])
        ended = claim(third, "driver_win_streak")
        self.assertEqual((ended["category"], ended["before"], ended["after"]), ("ENDED STREAKS", 2, 0))

    def test_tie_is_not_broken_and_joint_holders_retained(self):
        result = reports(fixture(("a", "b", "a")))
        tied = claim(result[1], "driver_wins")
        self.assertTrue(tied["tied"])
        self.assertEqual(tied["category"], "NEW RECORDS")
        self.assertEqual(claim(result[2], "driver_wins")["previous_holders"], ["a", "b"])

    def test_joint_holders_can_jointly_extend_a_benchmark(self):
        result = reports(fixture(("a", "a")))
        joint = claim(result[1], "driver_podiums")
        self.assertEqual(joint["category"], "BROKEN RECORDS")
        self.assertEqual((joint["before"], joint["after"]), (1, 2))
        self.assertTrue(joint["tied"])
        self.assertTrue(joint["self_extension"])

    def test_missing_fields_disable_universal_comparisons(self):
        data = fixture()
        for event in data["events"]:
            event["results"][0]["date_of_birth"] = None
            # Keep driver identities consistent by removing all birth dates.
            for row in event["results"]:
                row["date_of_birth"] = None
                row["grid"] = None
        last = reports(data)[-1]
        self.assertIn("youngest_winner", last["disabled_rules"])
        self.assertIn("positions_gained", last["disabled_rules"])
        self.assertNotIn("winning_grid", {c["rule_id"] for c in last["claims"]})

    def test_constructor_renames_not_merged(self):
        data = fixture(("a", "a"))
        for row in data["events"][1]["results"]:
            if row["constructor_id"] == "red":
                row["constructor_id"] = "new_red"
        c = claim(reports(data)[1], "constructor_wins")
        self.assertEqual(c["after"], 1)
        self.assertTrue(c["tied"])

    def test_absence_breaks_calendar_streak(self):
        data = fixture()
        data["events"][2]["results"] = [r for r in data["events"][2]["results"] if r["driver_id"] != "a"]
        for pos, row in enumerate(data["events"][2]["results"], 1):
            row["position"] = pos
        ended = [c for c in reports(data)[2]["claims"] if c["rule_id"] == "driver_points_streak" and c["category"] == "ENDED STREAKS"]
        self.assertEqual(ended[0]["entities"], ["a"])
        self.assertEqual(ended[0]["before"], 2)

    def test_qualifying_does_not_override_grid(self):
        data = fixture(("a",))
        data["events"][0]["results"][0]["qualifying_position"] = 1
        self.assertEqual(claim(reports(data)[0], "winning_grid")["after"], 4)

    def test_appeal_remains_provisional_and_confirmation_requires_evidence(self):
        data = fixture(("a",))
        data["events"][0]["official_status"] = "final"
        self.assertEqual(reports(data)[0]["verification"], "provisional")
        data["events"][0]["verification"] = "confirmed"
        with self.assertRaises(DataError):
            validate(data)

    def test_sprint_future_partial_duplicate_and_incomplete_history_rejected(self):
        cases = []
        data = fixture(); data["events"][0]["session"] = "sprint"; cases.append(data)
        data = fixture(); data["events"][0]["completed"] = False; cases.append(data)
        data = fixture(); data["events"].pop(1); cases.append(data)
        data = fixture(); data["events"][0]["results"].append(data["events"][0]["results"][0]); cases.append(data)
        data = fixture(); data["events"][0]["results"][0]["points"] = "NaN"; cases.append(data)
        for data in cases:
            with self.subTest(data=data), self.assertRaises((DataError, ValueError)):
                validate(data)

    def test_language_rendering_and_bounded_claims(self):
        report = dict(reports(fixture())[0], revision=1, kind="new")
        for language, marker in (("zh", "车手胜场"), ("en", "Driver GP wins"), ("bilingual", "车手胜场 / Driver GP wins")):
            output = render(report, language)
            self.assertIn(marker, output)
            self.assertIn("PROVISIONAL", output)
            self.assertIn("HISTORICAL CONTEXT", output)


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(self.tmp.name)

    def tearDown(self):
        self.store.__exit__()
        self.tmp.cleanup()

    def test_first_run_latest_only_noop_and_two_event_catchup(self):
        self.assertEqual(self.store.execute(lambda: fixture(("a", "a"))), ["2024-02-gp:r1"])
        self.assertEqual(self.store.execute(lambda: fixture(("a", "a"))), [])
        self.assertEqual(self.store.status()["latest_run"]["status"], "noop")
        self.assertEqual(self.store.execute(fixture), ["2024-03-gp:r1", "2024-04-gp:r1"])
        self.assertEqual(len(self.store.outbox()), 3)

    def test_retrieval_time_does_not_create_revisions(self):
        self.store.execute(fixture, backfill=True)
        later = fixture()
        for event in later["events"]:
            event["sources"][0]["retrieved_at"] = "2024-05-01T00:00:00Z"
        self.assertEqual(self.store.execute(lambda: later), [])
        self.assertEqual(self.store.status()["event_versions"], 4)

    def test_dsq_recomputes_downstream_and_preserves_history(self):
        self.store.execute(fixture, backfill=True)
        changed = fixture()
        rows = changed["events"][1]["results"]
        rows[0].update(position=None, points="0", disqualified=True, finished=False)
        for row in rows[1:]:
            row["position"] -= 1
            row["points"] = str([25, 18, 15][row["position"] - 1])
        revisions = self.store.execute(lambda: changed)
        self.assertIn("2024-02-gp:r2", revisions)
        self.assertIn("2024-04-gp:r2", revisions)
        last = json.loads(self.store.latest("reports")["2024-04-gp"]["payload"])
        self.assertEqual(claim(last, "driver_wins")["after"], 2)
        self.assertEqual(last["kind"], "correction")
        self.assertTrue((Path(self.tmp.name) / "reports/2024-02-gp/r1.json").exists())
        self.assertEqual(self.store.execute(lambda: changed), [])

    def test_crash_in_transaction_rolls_back_everything(self):
        with patch("f1tracker.store.evaluate", side_effect=RuntimeError("simulated crash")):
            with self.assertRaises(RuntimeError):
                self.store.execute(fixture)
        self.assertEqual(self.store.status()["event_versions"], 0)
        self.assertEqual(self.store.outbox(), [])
        self.assertEqual(self.store.status()["latest_run"]["status"], "failed")
        self.assertEqual(self.store.execute(fixture), ["2024-04-gp:r1"])

    def test_export_crash_recovered_without_duplicate_notifications(self):
        with patch("f1tracker.store.os.replace", side_effect=OSError("disk failure")):
            with self.assertRaises(OSError):
                self.store.execute(fixture)
        self.assertEqual(len(self.store.outbox()), 1)
        self.assertEqual(self.store.execute(fixture), [])
        self.assertTrue((Path(self.tmp.name) / "reports/2024-04-gp/r1.zh.md").exists())
        self.assertEqual(len(self.store.outbox()), 1)

    def test_source_failure_keeps_previous_success_and_logs_failure(self):
        self.store.execute(fixture)
        prior = self.store.db.execute("SELECT value FROM meta WHERE key='last_successful_check_at'").fetchone()[0]
        def failure():
            raise DataError("source timeout")
        with self.assertRaises(DataError):
            self.store.execute(failure)
        self.assertEqual(prior, self.store.db.execute("SELECT value FROM meta WHERE key='last_successful_check_at'").fetchone()[0])
        self.assertEqual(self.store.status()["latest_run"]["status"], "failed")

    def test_scope_shrink_lock_and_ack(self):
        self.store.execute(fixture)
        with self.assertRaises(DataError):
            self.store.execute(lambda: fixture(("a",)))
        with self.assertRaises(DataError):
            Store(self.tmp.name)
        self.store.acknowledge("2024-04-gp:r1")
        self.store.acknowledge("2024-04-gp:r1")
        self.assertEqual(self.store.outbox(), [])

    def test_correction_supersedes_only_undelivered_revision(self):
        self.store.execute(fixture, backfill=True)
        self.store.acknowledge("2024-01-gp:r1")
        revised = fixture(("b", "a", "b", "a"))
        self.store.execute(lambda: revised)
        pending = {row["notification_id"] for row in self.store.outbox()}
        self.assertIn("2024-01-gp:r2", pending)
        self.assertNotIn("2024-02-gp:r1", pending)
        self.assertEqual(self.store.db.execute("SELECT state FROM outbox WHERE notification_id='2024-01-gp:r1'").fetchone()[0], "acknowledged")
        with self.assertRaises(DataError):
            self.store.acknowledge("2024-02-gp:r1")

    def test_corrupt_or_newer_database_never_silently_resets(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tracker.sqlite3"
            path.write_bytes(b"not a SQLite database")
            with self.assertRaises(sqlite3.DatabaseError):
                Store(directory)
            self.assertEqual(path.read_bytes(), b"not a SQLite database")

    def test_restart_marks_incomplete_run_interrupted(self):
        with self.store.db:
            self.store.db.execute("INSERT INTO runs VALUES ('crash','2024-01-01T00:00:00Z',NULL,'running',NULL)")
        self.store.__exit__()
        self.store = Store(self.tmp.name)
        self.assertEqual(self.store.status()["latest_run"]["status"], "interrupted")

    def test_backup_is_restorable(self):
        self.store.execute(fixture)
        destination = Path(self.tmp.name) / "backup.sqlite3"
        self.store.backup(destination)
        with sqlite3.connect(destination) as db:
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(db.execute("SELECT count(*) FROM reports").fetchone()[0], 1)


def api_race():
    return {"season": "2024", "round": "1", "raceName": "Synthetic GP", "date": "2024-03-07", "time": "15:00:00Z",
            "Results": [{"position": str(p), "points": str(points), "grid": str(p), "status": "Finished",
                         "Driver": {"driverId": d, "givenName": d, "familyName": "Test", "dateOfBirth": "1990-01-01"},
                         "Constructor": {"constructorId": "red" if p < 3 else "blue"}}
                        for p, (d, points) in enumerate(zip("abcd", (25, 18, 15, 0)), 1)]}


def response(races, total, offset=0):
    return {"MRData": {"series": "f1", "offset": str(offset), "total": str(total), "RaceTable": {"Races": races}}}


class FakeClient:
    def __init__(self, responses):
        self.responses = iter(responses)

    def get(self, url):
        return copy.deepcopy(next(self.responses))


class SourceTests(unittest.TestCase):
    def test_split_race_across_pages_and_normalization(self):
        race = api_race()
        a, b = copy.deepcopy(race), copy.deepcopy(race)
        a["Results"], b["Results"] = a["Results"][:2], b["Results"][2:]
        found = pages(FakeClient([response([a], 4), response([b], 4, 2)]), "2024/results", True)
        self.assertEqual(len(found[("2024", "1")]["Results"]), 4)
        calendar = {k: v for k, v in race.items() if k != "Results"}
        snapshot = sync(FakeClient([response([calendar], 1), response([race], 4)]), 2024, 2024,
                        now=datetime(2024, 3, 8, tzinfo=timezone.utc))
        self.assertEqual(validate(snapshot)["events"][0]["verification"], "provisional")

    def test_stale_landing_wrong_season_and_missing_results(self):
        calendar = {k: v for k, v in api_race().items() if k != "Results"}
        with self.assertRaisesRegex(DataError, "Coverage incomplete"):
            sync(FakeClient([response([calendar], 1), response([], 0)]), 2024, 2024,
                 now=datetime(2024, 3, 8, tzinfo=timezone.utc))
        calendar["season"] = "2023"
        with self.assertRaisesRegex(DataError, "wrong season"):
            sync(FakeClient([response([calendar], 1), response([], 0)]), 2024, 2024)

    def test_changing_pagination_rejected(self):
        race = api_race()
        with self.assertRaises(DataError):
            pages(FakeClient([response([race], 8), response([race], 9, 4)]), "2024/results", True)

    def test_grid_zero_is_unknown_and_dns_is_not_a_start(self):
        race = api_race()
        race["Results"][-1].update(grid="0", status="Did not start")
        row = normalize(race, "2024-03-08T00:00:00Z")["results"][-1]
        self.assertIsNone(row["grid"])
        self.assertIsNone(row["position"])
        self.assertFalse(row["started"])

    def test_http_retry_and_permanent_denial(self):
        with tempfile.TemporaryDirectory() as directory:
            attempts = []
            def unavailable(request, timeout):
                attempts.append(request)
                raise urllib.error.HTTPError(request.full_url, 503, "Unavailable", {}, None)
            with self.assertRaises(DataError):
                Client(directory, unavailable, sleep=lambda _: None).get("https://example.org/")
            self.assertEqual(len(attempts), 3)
            self.assertIn("F1KnowledgeTracker", attempts[0].get_header("User-agent"))
            attempts.clear()
            def denied(request, timeout):
                attempts.append(request)
                raise urllib.error.URLError("Tunnel connection failed: 403 Forbidden")
            with self.assertRaises(DataError):
                Client(directory, denied, sleep=lambda _: None).get("https://example.org/")
            self.assertEqual(len(attempts), 1)

    def test_cli_noop_silent_and_invalid_input_nonzero(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.json"
            source.write_text(json.dumps(fixture()))
            args = ["--data-dir", str(Path(directory) / "data"), "import", str(source)]
            with patch("sys.stdout", new_callable=io.StringIO) as output:
                self.assertEqual(main(args), 0)
                self.assertIn("changed_reports", output.getvalue())
            with patch("sys.stdout", new_callable=io.StringIO) as output:
                self.assertEqual(main(args), 0)
                self.assertEqual(output.getvalue(), "")
            source.write_text("{}")
            with patch("sys.stderr", new_callable=io.StringIO) as error:
                self.assertEqual(main(args), 1)
                self.assertIn("Malformed snapshot", error.getvalue())


if __name__ == "__main__":
    unittest.main()
