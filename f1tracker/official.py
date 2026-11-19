"""Conservative official-page comparison. Agreement never clears appeals."""
import hashlib
from html.parser import HTMLParser
import re
import unicodedata
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from .model import require, utcnow
from .verification import fingerprint

SLUGS = dict(zip(
    ['Bahrain','Saudi Arabian','Australian','Japanese','Chinese','Miami','Emilia Romagna','Monaco','Canadian','Spanish','Austrian','British','Hungarian','Belgian','Dutch','Italian','Azerbaijan','Singapore','United States','Mexico City','São Paulo','Las Vegas','Qatar','Abu Dhabi'],
    ['bahrain','saudi-arabia','australia','japan','china','miami','emilia-romagna','monaco','canada','spain','austria','great-britain','hungary','belgium','netherlands','italy','azerbaijan','singapore','united-states','mexico','brazil','las-vegas','qatar','abu-dhabi']))


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.links, self.text = [], [], []
        self.row = self.cell = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and attrs.get('href'):
            self.links.append(attrs['href'])
        if tag == 'tr':
            self.row = []
        if tag in ('td', 'th'):
            self.cell = []

    def handle_data(self, value):
        self.text.append(value)
        if self.cell is not None:
            self.cell.append(value)

    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None:
            if self.row is not None:
                self.row.append(' '.join(' '.join(self.cell).split()))
            self.cell = None
        if tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def name(value):
    key = re.sub('[^a-z0-9]', '', unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().lower())
    return 'zhouguanyu' if key == 'guanyuzhou' else key


def fetch(url):
    parts = urlsplit(url)
    require(parts.scheme == 'https' and parts.hostname in ('www.formula1.com', 'www.fia.com'), 'Unsupported official host')
    with urlopen(Request(url, headers={'User-Agent': 'F1KnowledgeTracker/0.2.0'}), timeout=25) as response:
        require(urlsplit(response.geturl()).hostname == parts.hostname and response.geturl().startswith('https://'), 'Unexpected official redirect')
        require(response.geturl().rstrip('/') == url.rstrip('/'), 'Official page redirected; verify the actual event URL')
        raw = response.read(5_000_001)
        require(len(raw) <= 5_000_000, 'Official document too large')
        return raw


def compare_results(event, url, raw):
    require(f'/en/results/{event["season"]}/races/' in url and url.endswith('/race-result'), 'Wrong season/session source')
    page = Page(); page.feed(raw.decode('utf-8'))
    slug = SLUGS.get(event['name'].removesuffix(' Grand Prix'))
    require(slug and urlsplit(url).path.split('/')[-2] == slug, 'Official page does not identify the expected event')
    rows = [r for r in page.rows if len(r) == 7 and r[1].isdigit()]
    require(len(rows) == len(event['results']), 'Incomplete official classification')
    by_name = {name(r['driver_name']): r for r in event['results']}
    require(len(by_name) == len(rows), 'Ambiguous driver identity')
    differences, seen, excluded_count = {'classification': [], 'points': []}, set(), 0
    for ordinal, row in enumerate(rows, 1):
        driver_name = name(' '.join(row[2].split()[:-1]))  # final token is the three-letter code
        require(driver_name in by_name and driver_name not in seen, 'Official driver identity mismatch')
        seen.add(driver_name)
        expected = by_name[driver_name]
        status = row[5].upper()
        excluded = row[0].upper() in ('DQ', 'DSQ') or status in ('DSQ', 'DQ', 'DNS')
        excluded_count += int(excluded)
        rank = None if excluded else int(row[0]) if row[0].isdigit() else ordinal - excluded_count
        if rank != expected['position']:
            differences['classification'].append(f'{expected["driver_id"]}: classification differs')
        from decimal import Decimal
        if Decimal(row[6]) != Decimal(expected['points']):
            differences['points'].append(f'{expected["driver_id"]}: GP points differ')
    checked = utcnow()
    evidence = [{'url': url, 'title': event['name'] + ' race result', 'publisher': 'Formula1.com',
                 'retrieved_at': checked, 'sha256': hashlib.sha256(raw).hexdigest()}]
    return [{'event_id': event['event_id'], 'capability': cap, 'fingerprint': fingerprint(event, cap),
             'status': 'blocked' if differences[cap] else 'matched', 'reviewer': 'formula1-table-comparator/1',
             'checked_at': checked, 'note': '; '.join(differences[cap]) if differences[cap] else
             'Official table agrees with imported results; FIA decisions and independent review remain required',
             'evidence': evidence} for cap in ('classification', 'points')]


def fia_packet(event, url, raw):
    """Identify actual linked documents, without inventing PDF paths or appeal clearance."""
    from urllib.parse import urljoin, unquote, quote
    require(urlsplit(url).hostname == 'www.fia.com', 'FIA index required')
    require(f'season-{event["season"]}-' in url, 'FIA index must explicitly select the correct season')
    page = Page(); page.feed(raw.decode('utf-8'))
    prefix = name(str(event['season']) + event['name'])
    documents = []
    for href in page.links:
        path = unquote(urlsplit(href).path)
        if path.lower().endswith('.pdf') and name(path.rsplit('/', 1)[-1]).startswith(prefix):
            target = urljoin(url, quote(path, safe='/'))
            if urlsplit(target).hostname == 'www.fia.com':
                documents.append({'url': target, 'title': path.rsplit('/', 1)[-1]})
    require(documents, 'Index has no documents for the selected event; never accept a default older/different GP')
    return {'event_id': event['event_id'], 'index_url': url, 'retrieved_at': utcnow(),
            'index_sha256': hashlib.sha256(raw).hexdigest(), 'documents': documents,
            'review_candidates': [d for d in documents if any(word in d['title'].lower()
                                  for word in ('decision', 'infringement', 'appeal', 'protest', 'review', 'amended'))],
            'decision_clearance': 'unreviewed',
            'note': 'Inspect final classifications, revisions and open proceedings; an index is not appeal clearance'}


def inspect_fia_final(event, raw):
    """Extract a final PDF's identity and podium; legal status is still reviewed separately."""
    import subprocess
    import tempfile
    from pathlib import Path
    require(raw.startswith(b'%PDF'), 'FIA response is not a PDF')
    with tempfile.TemporaryDirectory() as directory:
        pdf = Path(directory) / 'source.pdf'; pdf.write_bytes(raw)
        result = subprocess.run(['pdftotext', '-layout', str(pdf), '-'], capture_output=True, text=True, timeout=30, check=True)
    text = result.stdout
    require(name(str(event['season']) + event['name']) in name(text[:2000]), 'PDF year/event mismatch')
    require('Final Race Classification' in text[:2000], 'PDF is not a final GP classification')
    rows = re.findall(r'^\s*([123])\s+\d+\s+(.+?)\s{2,}', text, re.M)
    require(len(rows) == 3, 'Ambiguous or missing FIA podium rows')
    actual = {int(pos): name(driver) for pos, driver in rows}
    expected = {r['position']: name(r['driver_name']) for r in event['results'] if r['position'] in (1, 2, 3)}
    number = re.search(r'Document\s+(\d+)', text[:2000])
    return {'document_number': number[1] if number else None,
            'sha256': hashlib.sha256(raw).hexdigest(), 'podium_match': actual == expected,
            'official_status': 'final', 'decision_clearance': 'unreviewed',
            'scope': 'PDF identity and podium only; no automatic appeal clearance'}


def verify_season(store, season):
    import json
    import time
    from .store import atomic_write
    index = fetch(f'https://www.formula1.com/en/results/{season}/races')
    page = Page(); page.feed(index.decode('utf-8'))
    links = sorted(set(x for x in page.links if f'/en/results/{season}/races/' in x and x.endswith('/race-result')))
    events = [json.loads(r['payload']) for r in store.latest('event_versions').values()]
    events = [e for e in events if e['season'] == season]
    require(events, 'Import the selected season first')
    require(len(links) == len(events), 'Official calendar/imported event coverage mismatch')
    checks = []
    for event in events:
        try:
            slug = SLUGS[event['name'].removesuffix(' Grand Prix')]
            matches = [x for x in links if x.split('/')[-2] == slug]
            require(len(matches) == 1, 'Ambiguous event page')
            url = 'https://www.formula1.com' + matches[0]
            raw = fetch(url)
            atomic_write(store.directory / 'official-evidence' / (hashlib.sha256(raw).hexdigest()+'.html'), raw.decode())
            reviews = compare_results(event, url, raw)
            store.add_reviews(reviews)
            checks.append({'event_id': event['event_id'], 'status': 'matched' if all(r['status']=='matched' for r in reviews) else 'blocked',
                           'url': url, 'details': [r['note'] for r in reviews]})
        except (ValueError, KeyError, OSError) as exc:
            checks.append({'event_id': event['event_id'], 'status': 'error', 'detail': str(exc)})
        time.sleep(0.3)
    atomic_write(store.directory / f'baseline-{season}.json', json.dumps(checks, ensure_ascii=False, indent=2))
    return checks
