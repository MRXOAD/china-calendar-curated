"""Read Apple's public mainland-China calendar to identify covered occasions."""

from datetime import date, datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import urllib.request

from icalendar import Calendar


SOURCE_URL = 'https://calendars.icloud.com/holidays/cn_zh.ics'
REFERENCE_PATH = Path(__file__).resolve().parent / 'data' / 'apple_covered.json'
ALIASES = {'七夕节': '七夕', '清明节': '清明'}


def occasion_name(name: str) -> str:
    name = unicodedata.normalize('NFKC', name).strip()
    name = re.sub(r'\((?:休|班)\)$', '', name).strip()
    return ALIASES.get(name, name)


def parse_reference(raw: bytes) -> dict:
    calendar = Calendar.from_ical(raw)
    if calendar.name != 'VCALENDAR' or str(calendar.get('X-WR-CALNAME', '')) != '中国大陆节假日':
        raise ValueError('Expected Apple mainland-China holiday calendar')
    events = calendar.walk('VEVENT')
    if not events:
        raise ValueError('Apple holiday calendar contains no events')
    names = set()
    years = set()
    for event in events:
        if event.errors or not event.get('SUMMARY') or not event.get('DTSTART'):
            raise ValueError('Apple holiday calendar contains an invalid event')
        start = event.decoded('DTSTART')
        if type(start) is not date:
            raise ValueError('Expected all-day dates in Apple holiday calendar')
        names.add(occasion_name(str(event['SUMMARY'])))
        years.add(start.year)
    return {
        'source_url': SOURCE_URL,
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'sha256': hashlib.sha256(raw).hexdigest(),
        'event_count': len(events),
        'source_years': sorted(years),
        'covered_names': sorted(names),
    }


def load_covered_names() -> set[str]:
    reference = json.loads(REFERENCE_PATH.read_text(encoding='utf-8'))
    names = reference['covered_names']
    if reference['source_url'] != SOURCE_URL or not names or not all(isinstance(name, str) and name for name in names):
        raise ValueError('Invalid Apple calendar reference')
    return set(names)


def refresh_reference() -> None:
    request = urllib.request.Request(SOURCE_URL, headers={'Accept': 'text/calendar'})
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read()
        if response.headers.get('Content-Encoding', '').lower() == 'gzip':
            raw = gzip.decompress(raw)
    reference = parse_reference(raw)
    if REFERENCE_PATH.exists():
        # Keep exclusions already recorded in the checked-in reference when
        # Apple's rolling date window drops the year containing that occasion.
        reference['covered_names'] = sorted(set(reference['covered_names']) | load_covered_names())
    # Validate before writing. A download/parse failure stops publication;
    # the last deployed feed is retained by GitHub Pages.
    REFERENCE_PATH.write_text(json.dumps(reference, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"Checked {reference['event_count']} Apple events; {len(reference['covered_names'])} covered occasions")


if __name__ == '__main__':
    refresh_reference()
