import copy
import json
import tempfile
import unittest
from test_tracker import fixture
from f1tracker.store import Store
from f1tracker.verification import fingerprint, requirements
from f1tracker.model import DataError
from f1tracker.official import compare_results, fia_packet
from f1tracker.official import inspect_fia_final
from unittest.mock import patch
from types import SimpleNamespace


def review(event, cap):
    return {'event_id': event['event_id'], 'capability': cap, 'fingerprint': fingerprint(event, cap),
            'status': 'confirmed', 'reviewer': 'synthetic-test-reviewer', 'checked_at': '2024-04-02T00:00:00Z',
            'note': 'Synthetic evidence, not a real audit', 'official_status': 'final', 'open_cases': [],
            'evidence': [{'url': 'https://www.fia.com/synthetic-test-only.pdf', 'title': 'Synthetic fixture',
                          'publisher': 'Synthetic test', 'sha256': 'a'*64, 'retrieved_at': '2024-04-02T00:00:00Z'}]}


class ReviewTests(unittest.TestCase):
    def test_final_pdf_checks_event_podium_and_preserves_legal_gap(self):
        event=fixture(('a',))['events'][0];event['name']='Bahrain Grand Prix'
        for row in event['results']:row['driver_name']='Driver '+row['driver_id']
        text='2024 BAHRAIN GRAND PRIX\nDocument 57\nFinal Race Classification\n 1 4 Driver a  Team\n 2 5 Driver b  Team\n 3 6 Driver c  Team\n'
        with patch('subprocess.run',return_value=SimpleNamespace(stdout=text)):
            result=inspect_fia_final(event,b'%PDF-test')
            self.assertTrue(result['podium_match'])
            self.assertEqual(result['decision_clearance'],'unreviewed')
        with patch('subprocess.run',return_value=SimpleNamespace(stdout=text.replace('2024','2025'))):
            with self.assertRaises(DataError):inspect_fia_final(event,b'%PDF-test')

    def test_official_comparison_does_not_clear_decisions(self):
        event = fixture(('a',))['events'][0]
        event['name'] = 'Bahrain Grand Prix'
        rows = []
        for row in event['results']:
            row['driver_name'] = 'Driver ' + row['driver_id']
            cells = [str(row['position']), str(row['position']), row['driver_name']+' XXX', 'Team', '50', 'Finished', row['points']]
            rows.append('<tr>'+''.join('<td>'+c+'</td>' for c in cells)+'</tr>')
        raw = ('<table>'+''.join(rows)+'</table>').encode()
        url = 'https://www.formula1.com/en/results/2024/races/1229/bahrain/race-result'
        result = compare_results(event, url, raw)
        self.assertEqual({r['status'] for r in result}, {'matched'})
        self.assertEqual({r['capability'] for r in result}, {'classification', 'points'})
        with self.assertRaises(DataError): compare_results(event, url.replace('/2024/', '/2025/'), raw)
        with self.assertRaises(DataError): compare_results(event, url.replace('/bahrain/', '/monaco/'), raw)

    def test_fia_index_cannot_confirm_another_event(self):
        event = fixture(('a',))['events'][0]; event['name'] = 'Bahrain Grand Prix'
        url = 'https://www.fia.com/documents/season/season-2024-2043'
        raw = b'<a href="/sites/default/files/2024 Abu Dhabi Grand Prix - Final Race Classification.pdf">Final</a>'
        with self.assertRaises(DataError): fia_packet(event, url, raw)
        packet = fia_packet(event, url, raw.replace(b'Abu Dhabi', b'Bahrain'))
        self.assertEqual(packet['decision_clearance'], 'unreviewed')

    def test_identical_review_new_retrieval_does_not_duplicate(self):
        with tempfile.TemporaryDirectory() as directory, Store(directory) as store:
            data=fixture();store.execute(lambda:data)
            r=review(data['events'][0], 'classification');store.add_reviews([r])
            r['checked_at']='2024-05-01T00:00:00Z';r['evidence'][0]['retrieved_at']=r['checked_at']
            self.assertEqual(store.add_reviews([r]), [])
            self.assertEqual(store.db.execute('SELECT count(*) FROM reviews').fetchone()[0],1)

    def test_persistent_partial_verification_and_scope(self):
        with tempfile.TemporaryDirectory() as directory, Store(directory) as store:
            data = fixture()
            store.execute(lambda: data)
            reviews = [review(e, cap) for e in data['events'] for cap in requirements('driver_wins')]
            store.add_reviews(reviews)
            report = json.loads(store.latest('reports')['2024-04-gp']['payload'])
            self.assertEqual(report['verification'], 'mixed')
            wins = next(c for c in report['claims'] if c['rule_id'] == 'driver_wins')
            self.assertEqual(wins['verification'], 'confirmed')
            points = next(c for c in report['claims'] if c['rule_id'] == 'driver_points')
            self.assertEqual(points['verification'], 'provisional')
            self.assertEqual({g['capability'] for g in points['verification_gaps']}, {'points'})
            self.assertEqual(store.execute(lambda: data), [])
            self.assertEqual(store.review_status()[0]['capabilities']['classification'], 'confirmed')

    def test_fact_changes_invalidate_only_related_reviews(self):
        with tempfile.TemporaryDirectory() as directory, Store(directory) as store:
            data = fixture()
            store.execute(lambda: data)
            store.add_reviews([review(e, cap) for e in data['events'] for cap in ('classification', 'decisions', 'birth_dates')])
            revised = copy.deepcopy(data)
            for e in revised['events']:
                for row in e['results']:
                    if row['driver_id'] == 'a': row['date_of_birth'] = '1991-01-01'
            store.execute(lambda: revised)
            statuses = store.review_status()[0]['capabilities']
            self.assertEqual(statuses['classification'], 'confirmed')
            self.assertEqual(statuses['birth_dates'], 'stale')
            # A changed result invalidates decision clearance as well.
            revised['events'][0]['results'][0]['points'] = '24'
            store.execute(lambda: revised)
            self.assertEqual(store.review_status()[0]['capabilities']['decisions'], 'stale')

    def test_open_appeals_and_stale_import_rejected(self):
        with tempfile.TemporaryDirectory() as directory, Store(directory) as store:
            data = fixture(); store.execute(lambda: data)
            pending = review(data['events'][0], 'decisions'); pending['open_cases'] = ['appeal']
            with self.assertRaises(DataError): store.add_reviews([pending])
            stale = review(data['events'][0], 'classification'); stale['fingerprint'] = '0'*64
            with self.assertRaises(DataError): store.add_reviews([stale])
            self.assertEqual(store.db.execute('SELECT count(*) FROM reviews').fetchone()[0], 0)

    def test_reopen_preserves_review_history(self):
        with tempfile.TemporaryDirectory() as directory:
            with Store(directory) as store:
                data = fixture(); store.execute(lambda: data)
                store.add_reviews([review(data['events'][0], 'classification')])
            with Store(directory) as store:
                self.assertEqual(store.review_status()[0]['capabilities']['classification'], 'confirmed')
                self.assertEqual(store.db.execute('PRAGMA user_version').fetchone()[0], 2)
