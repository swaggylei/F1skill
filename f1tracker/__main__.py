import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys
import subprocess

from .model import DataError
from .rules import RULES
from .source import Client, sync
from .store import Store
from .verification import FIELDS, fingerprint
from .official import compare_results, fetch, fia_packet, inspect_fia_final, verify_season


def main(argv=None):
    parser = argparse.ArgumentParser(description="Bounded-scope GP record tracker; Python 3.10+, Linux/macOS")
    parser.add_argument("--data-dir", default=os.environ.get("F1_KNOWLEDGE_DATA_DIR", "./f1-knowledge-data"))
    parser.add_argument("--language", choices=("zh", "en", "bilingual"), default="zh")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("rules", help="Show the 20 versioned metric definitions")
    importer = commands.add_parser("import", help="Import a complete normalized snapshot")
    importer.add_argument("file", type=Path)
    importer.add_argument("--backfill", action="store_true", help="Also report historical baseline events")
    live = commands.add_parser("sync", help="Fetch and recheck all GP results in the configured range")
    live.add_argument("--start-year", type=int, required=True)
    live.add_argument("--end-year", type=int, required=True)
    live.add_argument("--backfill", action="store_true")
    for name in ("status", "export", "outbox"):
        commands.add_parser(name)
    commands.add_parser("ack", help="Mark notification acknowledged after confirmed external delivery").add_argument("notification_id")
    commands.add_parser("backup", help="Consistent SQLite backup to a new path").add_argument("destination", type=Path)
    commands.add_parser('review-status', help='Per-event evidence coverage and stale reviews')
    commands.add_parser('verify-season', help='Compare imported season with official race-result tables').add_argument('season', type=int)
    commands.add_parser('review-import', help='Import explicit evidence reviews').add_argument('file', type=Path)
    template = commands.add_parser('review-template', help='Print a review template; never auto-confirm')
    template.add_argument('event_id')
    template.add_argument('capability', choices=tuple(FIELDS))
    official = commands.add_parser('verify-official', help='Compare a specific Formula1.com race-result page')
    official.add_argument('event_id')
    official.add_argument('url')
    fia = commands.add_parser('collect-fia', help='Collect a correctly scoped FIA document manifest for review')
    fia.add_argument('event_id')
    fia.add_argument('url')
    fia.add_argument('--download-finals', action='store_true', help='Download actual linked final PDFs and check identity/podium; requires pdftotext')
    args = parser.parse_args(argv)
    try:
        if args.command == "rules":
            print(json.dumps(list(RULES.values()), ensure_ascii=False, indent=2))
            return 0
        with Store(args.data_dir) as store:
            if args.command in ("import", "sync"):
                if args.command == "import":
                    def loader():
                        return json.loads(args.file.read_text(encoding="utf-8"))
                else:
                    def loader():
                        return sync(Client(Path(args.data_dir) / "source-cache"), args.start_year, args.end_year)
                changed = store.execute(loader, args.backfill, args.language)
                if changed:
                    print(json.dumps({"changed_reports": changed}, ensure_ascii=False))
                # A verified no-op is deliberately silent. Failures go to stderr.
            elif args.command == "export":
                store.export(args.language)
            elif args.command in ("status", "outbox"):
                print(json.dumps(getattr(store, args.command)(), ensure_ascii=False, indent=2))
            elif args.command == "ack":
                store.acknowledge(args.notification_id)
            elif args.command == "backup":
                store.backup(args.destination)
            elif args.command == 'review-status':
                print(json.dumps(store.review_status(), ensure_ascii=False, indent=2))
            elif args.command == 'verify-season':
                checks = verify_season(store, args.season)
                print(json.dumps(checks, ensure_ascii=False, indent=2))
                return 0 if all(c['status'] == 'matched' for c in checks) else 1
            elif args.command == 'review-import':
                print(json.dumps({'changed_reports': store.add_reviews(json.loads(args.file.read_text()))}))
            elif args.command in ('review-template', 'verify-official', 'collect-fia'):
                event = json.loads(store.latest('event_versions')[args.event_id]['payload'])
                if args.command == 'review-template':
                    print(json.dumps([{'event_id': args.event_id, 'capability': args.capability,
                        'fingerprint': fingerprint(event, args.capability), 'status': 'blocked',
                        'reviewer': '', 'checked_at': '', 'note': '', 'evidence': []}], indent=2))
                else:
                    raw = fetch(args.url)
                    from .store import atomic_write
                    import hashlib
                    atomic_write(store.directory / 'official-evidence' / (hashlib.sha256(raw).hexdigest()+'.html'), raw.decode('utf-8'))
                    if args.command == 'collect-fia':
                        packet = fia_packet(event, args.url, raw)
                        if args.download_finals:
                            packet['finals'] = []
                            for document in packet['documents']:
                                if 'final race classification' in document['title'].lower():
                                    pdf = fetch(document['url'])
                                    check = inspect_fia_final(event, pdf)
                                    (store.directory / 'official-evidence' / (check['sha256']+'.pdf')).write_bytes(pdf)
                                    packet['finals'].append(dict(document, **check))
                        atomic_write(store.directory / 'official-evidence' / (args.event_id+'-fia.json'), json.dumps(packet, ensure_ascii=False, indent=2))
                        print(json.dumps(packet, ensure_ascii=False))
                        if args.download_finals and (not packet['finals'] or not all(d['podium_match'] for d in packet['finals'])):
                            return 1
                    else:
                        reviews = compare_results(event, args.url, raw)
                        print(json.dumps({'changed_reports': store.add_reviews(reviews), 'reviews': reviews}, ensure_ascii=False))
                        if any(r['status'] == 'blocked' for r in reviews):
                            return 1
        return 0
    except (DataError, ValueError, KeyError, TypeError, OSError, sqlite3.Error, subprocess.SubprocessError) as exc:
        print(f"f1tracker: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
