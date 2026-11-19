"""Evidence reviews are independent of API observations and scoped to facts."""
from urllib.parse import urlsplit
from .model import digest, require, timestamp

FIELDS = {
    'classification': ('driver_id', 'position', 'started', 'disqualified'),
    'points': ('driver_id', 'points'),
    'constructors': ('driver_id', 'constructor_id'),
    'birth_dates': ('driver_id', 'date_of_birth'),
    'grid': ('driver_id', 'grid'),
    'finish': ('driver_id', 'finished'),
    'decisions': ('driver_id', 'position', 'points', 'started', 'disqualified'),
}


def fingerprint(event, capability):
    return digest({'event_id': event['event_id'], 'date': event['date'],
                   'facts': [{k: r[k] for k in FIELDS[capability]}
                             for r in sorted(event['results'], key=lambda r: r['driver_id'])]})


def requirements(rule):
    needed = {'classification', 'decisions'}
    if 'constructor' in rule:
        needed.add('constructors')
    if 'points' in rule:
        needed.add('points')
    if rule.startswith(('youngest_', 'oldest_')):
        needed.add('birth_dates')
    if rule in ('winning_grid', 'podium_grid', 'positions_gained'):
        needed.add('grid')
    if rule == 'positions_gained':
        needed.add('finish')
    return sorted(needed)


def validate_review(review, event):
    require(review['event_id'] == event['event_id'], 'Review event mismatch')
    cap = review['capability']
    require(cap in FIELDS, 'Unknown review capability')
    require(review['fingerprint'] == fingerprint(event, cap), 'Review refers to stale facts')
    require(review['status'] in ('confirmed', 'matched', 'blocked'), 'Invalid review status')
    require(isinstance(review['reviewer'], str) and review['reviewer'].strip(), 'Named reviewer required')
    require(isinstance(review['note'], str) and review['note'].strip(), 'Review rationale required')
    timestamp(review['checked_at'])
    require(review['evidence'], 'Evidence is required')
    for source in review['evidence']:
        url = urlsplit(source['url'])
        require(url.scheme == 'https' and url.hostname and not url.username and not url.password, 'Invalid evidence URL')
        require(source['title'] and source['publisher'], 'Evidence title and publisher required')
        timestamp(source['retrieved_at'])
        sha = source['sha256']
        require(len(sha) == 64 and all(c in '0123456789abcdef' for c in sha), 'Evidence SHA-256 required')
    if cap == 'decisions' and review['status'] == 'confirmed':
        require(review.get('official_status') == 'final' and review.get('open_cases') == [],
                'Decision clearance requires final classification and explicit no-open-cases assertion')
        require(any(urlsplit(s['url']).hostname in ('fia.com', 'www.fia.com') for s in review['evidence']),
                'FIA evidence required for decision clearance')
    if cap == 'birth_dates' and review['status'] == 'confirmed':
        require(all(r['date_of_birth'] is not None for r in event['results']), 'Birth dates are incomplete')


def claim_review(rule, history):
    gaps, refs = [], []
    for event in history:
        for cap in requirements(rule):
            review = event.get('_reviews', {}).get(cap)
            reason = 'missing evidence review'
            if review:
                if review['fingerprint'] != fingerprint(event, cap):
                    reason = 'facts changed; review stale'
                elif review['status'] == 'confirmed':
                    refs.append(review['review_id'])
                    continue
                else:
                    reason = review['status'] + ': ' + review['note']
            gaps.append({'event_id': event['event_id'], 'capability': cap, 'reason': reason})
    return {'verification': 'provisional' if gaps else 'confirmed',
            'verification_gaps': gaps, 'review_ids': sorted(set(refs))}
