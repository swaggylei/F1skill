"""Single-writer SQLite transactions, immutable revisions and recoverable exports."""
import fcntl
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import uuid
from contextlib import contextmanager

from .model import DataError, canonical, digest, semantic, utcnow, validate
from .report import render
from .rules import evaluate
from .verification import FIELDS, fingerprint, validate_review

DDL = """
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS event_versions(
 event_id TEXT NOT NULL, revision INTEGER NOT NULL, fingerprint TEXT NOT NULL,
 payload TEXT NOT NULL, observed_at TEXT NOT NULL, PRIMARY KEY(event_id, revision));
CREATE TABLE IF NOT EXISTS reports(
 event_id TEXT NOT NULL, revision INTEGER NOT NULL, fingerprint TEXT NOT NULL,
 payload TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY(event_id, revision));
CREATE TABLE IF NOT EXISTS outbox(
 notification_id TEXT PRIMARY KEY, event_id TEXT NOT NULL, revision INTEGER NOT NULL,
 kind TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'pending', acknowledged_at TEXT);
CREATE TABLE IF NOT EXISTS runs(
 run_id TEXT PRIMARY KEY, started_at TEXT NOT NULL, ended_at TEXT, status TEXT NOT NULL, detail TEXT);
CREATE TABLE IF NOT EXISTS reviews(
 review_id TEXT PRIMARY KEY, event_id TEXT NOT NULL, capability TEXT NOT NULL,
 payload TEXT NOT NULL, created_at TEXT NOT NULL);
"""


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".export-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


class Store:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = open(self.directory / ".writer.lock", "a")
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            self.lock.close()
            raise DataError("Another tracker process holds the writer lock") from exc
        try:
            self.db = sqlite3.connect(self.directory / "tracker.sqlite3", timeout=5)
            self.db.row_factory = sqlite3.Row
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("PRAGMA synchronous=FULL")
            version = self.db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1, 2):
                raise DataError(f"Unsupported database schema {version}; preserve data and migrate explicitly")
            self.db.executescript(DDL)
            self.db.execute("PRAGMA user_version=2")
            with self.db:
                self.db.execute("UPDATE runs SET status='interrupted', ended_at=? WHERE status='running'", (utcnow(),))
        except Exception:
            self.lock.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.db.close()
        self.lock.close()

    @contextmanager
    def run(self, action):
        run_id = str(uuid.uuid4())
        with self.db:
            self.db.execute("INSERT INTO runs VALUES (?,?,NULL,'running',?)", (run_id, utcnow(), action))
        try:
            yield run_id
        except Exception as exc:
            with self.db:
                self.db.execute("UPDATE runs SET status='failed', ended_at=?, detail=? WHERE run_id=?",
                                (utcnow(), f'{type(exc).__name__}: {exc}', run_id))
            raise

    def latest(self, table):
        assert table in ("event_versions", "reports")
        rows = self.db.execute(f"SELECT a.* FROM {table} a JOIN (SELECT event_id, max(revision) AS revision FROM {table} GROUP BY event_id) b USING(event_id,revision)")
        return {row["event_id"]: row for row in rows}

    def ingest(self, snapshot, backfill=False):
        snapshot = validate(snapshot)
        events, coverage = snapshot["events"], snapshot["coverage"]
        current = self.latest("event_versions")
        previous_reports = self.latest("reports")
        meta = self.db.execute("SELECT value FROM meta WHERE key='coverage'").fetchone()
        if meta:
            old_coverage = json.loads(meta[0])
            if old_coverage["start_season"] != coverage["start_season"] or old_coverage["label"] != coverage["label"]:
                raise DataError("Baseline scope changed; use a separate data directory for a new scope")
        if not set(current) <= {e["event_id"] for e in events}:
            raise DataError("Snapshot would remove existing events; retain history or use a new data directory")
        changed = []
        with self.db:
            stable_events = []
            for event in events:
                key = event["event_id"]
                old = current.get(key)
                fingerprint = digest(semantic(event))
                if old:
                    old_event = json.loads(old["payload"])
                    if any(old_event[k] != event[k] for k in ("date", "name", "season", "round")):
                        raise DataError("Event identity changed; calendar remapping needs explicit migration")
                if old and old["fingerprint"] == fingerprint:
                    stable_events.append(json.loads(old["payload"]))
                    continue
                rev = old["revision"] + 1 if old else 1
                self.db.execute("INSERT INTO event_versions VALUES (?,?,?,?,?)",
                                (key, rev, fingerprint, canonical(event), utcnow()))
                stable_events.append(event)
            first = not current
            new_ids = {e["event_id"] for e in events} - set(current)
            targets = set(previous_reports)
            targets.update(new_ids if not first else {events[-1]["event_id"]})
            if backfill:
                targets.update(e["event_id"] for e in events)
            reviews = self.review_map()
            evaluated_events = [dict(e, _reviews=reviews.get(e['event_id'], {})) for e in stable_events]
            for payload in evaluate(evaluated_events, coverage):
                key = payload["event_id"]
                if key not in targets:
                    continue
                old = previous_reports.get(key)
                fingerprint = digest(semantic(payload))
                if old and old["fingerprint"] == fingerprint:
                    continue
                rev = old["revision"] + 1 if old else 1
                payload.update(revision=rev, kind="correction" if old else "new", created_at=utcnow())
                self.db.execute("INSERT INTO reports VALUES (?,?,?,?,?)",
                                (key, rev, fingerprint, canonical(payload), utcnow()))
                notification_id = f"{key}:r{rev}"
                self.db.execute("UPDATE outbox SET state='superseded' WHERE event_id=? AND state='pending'", (key,))
                self.db.execute("INSERT INTO outbox(notification_id,event_id,revision,kind) VALUES (?,?,?,?)",
                                (notification_id, key, rev, payload["kind"]))
                changed.append(notification_id)
            self.db.execute("INSERT OR REPLACE INTO meta VALUES ('coverage', ?)", (canonical(coverage),))
            self.db.execute("INSERT OR REPLACE INTO meta VALUES ('last_successful_check_at', ?)", (utcnow(),))
        return changed

    def review_map(self):
        result = {}
        for row in self.db.execute('SELECT payload FROM reviews ORDER BY rowid'):
            review = json.loads(row[0])
            result.setdefault(review['event_id'], {})[review['capability']] = review
        return result

    def add_reviews(self, reviews):
        events = {key: json.loads(row['payload']) for key, row in self.latest('event_versions').items()}
        existing = self.review_map()
        checked = []
        for review in reviews:
            if review['event_id'] not in events:
                raise DataError('Unknown review event')
            validate_review(review, events[review['event_id']])
            value = {k: v for k, v in review.items() if k != 'review_id'}
            old = existing.get(review['event_id'], {}).get(review['capability'])
            def comparable(r):
                return semantic({k: v for k, v in r.items() if k not in ('review_id', 'checked_at')})
            if old and comparable(old) == comparable(value):
                continue
            value['review_id'] = digest(value)
            checked.append(value)
        with self.db:
            for value in checked:
                self.db.execute('INSERT OR IGNORE INTO reviews VALUES (?,?,?,?,?)',
                                (value['review_id'], value['event_id'], value['capability'], canonical(value), utcnow()))
        return self.refresh()

    def refresh(self):
        meta = self.db.execute("SELECT value FROM meta WHERE key='coverage'").fetchone()
        if not meta:
            raise DataError('Import a baseline before reviewing it')
        snapshot = {'schema_version': 1, 'coverage': json.loads(meta[0]),
                    'events': [json.loads(r['payload']) for r in self.latest('event_versions').values()]}
        return self.execute(lambda: snapshot)

    def review_status(self):
        reviews = self.review_map()
        return [{'event_id': key, 'capabilities': {
            cap: ('missing' if cap not in reviews.get(key, {}) else
                  'stale' if reviews[key][cap]['fingerprint'] != fingerprint(json.loads(row['payload']), cap)
                  else reviews[key][cap]['status']) for cap in FIELDS}}
                for key, row in self.latest('event_versions').items()]

    def export(self, language="zh"):
        for row in self.db.execute('SELECT review_id,payload FROM reviews'):
            atomic_write(self.directory / 'reviews' / (row['review_id'] + '.json'), row['payload'] + '\n')
        for row in self.db.execute("SELECT * FROM event_versions ORDER BY event_id, revision"):
            path = self.directory / "events" / row["event_id"] / f'r{row["revision"]}.json'
            atomic_write(path, json.dumps(json.loads(row["payload"]), ensure_ascii=False, indent=2) + "\n")
        for row in self.db.execute("SELECT * FROM reports ORDER BY event_id, revision"):
            report = json.loads(row["payload"])
            path = self.directory / "reports" / row["event_id"] / f'r{row["revision"]}'
            atomic_write(path.with_suffix(".json"), json.dumps(report, ensure_ascii=False, indent=2) + "\n")
            atomic_write(path.with_suffix(f".{language}.md"), render(report, language))

    def execute(self, loader, backfill=False, language="zh"):
        with self.run("sync/import") as run_id:
            changed = self.ingest(loader(), backfill=backfill)
            self.export(language)
            with self.db:
                self.db.execute("UPDATE runs SET status=?, ended_at=?, detail=? WHERE run_id=?",
                                ("success" if changed else "noop", utcnow(), canonical(changed), run_id))
        return changed

    def status(self):
        counts = {name: self.db.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
                  for name in ("event_versions", "reports", "runs")}
        counts["pending_notifications"] = self.db.execute("SELECT count(*) FROM outbox WHERE state='pending'").fetchone()[0]
        counts["latest_run"] = next((dict(r) for r in self.db.execute("SELECT * FROM runs ORDER BY rowid DESC LIMIT 1")), None)
        counts["pending_reviews"] = [key for key, row in self.latest("event_versions").items()
                                     if json.loads(row["payload"])["verification"] != "confirmed"]
        return counts

    def outbox(self):
        return [dict(r) for r in self.db.execute("SELECT * FROM outbox WHERE state='pending' ORDER BY rowid")]

    def acknowledge(self, notification_id):
        with self.db:
            row = self.db.execute("SELECT state FROM outbox WHERE notification_id=?", (notification_id,)).fetchone()
            if not row:
                raise DataError("Unknown notification ID")
            if row[0] == "superseded":
                raise DataError("Notification has been superseded; deliver the latest revision")
            if row[0] == "pending":
                self.db.execute("UPDATE outbox SET state='acknowledged', acknowledged_at=? WHERE notification_id=?",
                                (utcnow(), notification_id))

    def backup(self, destination):
        destination = Path(destination)
        if destination.exists():
            raise DataError("Backup destination already exists; refusing to overwrite")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(destination) as target:
            self.db.backup(target)
