from pathlib import Path
from io import BytesIO
import json
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

import generate
import apple_reference


class AppleOverlapTests(unittest.TestCase):
    def test_recommended_feed_omits_apples_occasions_in_every_year(self):
        # Confirmed in Apple's cn_zh.ics, including its 七夕节 spelling and
        # partial-population holidays found in the 2024 entries.
        covered = set(generate.TERM_NAMES) | {
            '元旦', '春节', '除夕', '清明节', '劳动节', '端午节', '中秋节', '国庆节',
            '元宵节', '七夕', '重阳节', '妇女节', '青年节', '儿童节',
        }
        with tempfile.TemporaryDirectory() as temp:
            feeds = generate.build(output=Path(temp))
        self.assertTrue(covered.isdisjoint(e.name for e in feeds['all.ics']))
        self.assertIn('腊八节', {e.name for e in feeds['all.ics']})
        self.assertIn('母亲节', {e.name for e in feeds['all.ics']})
        # Existing standalone feeds retain their explicitly separate purpose.
        self.assertEqual(len(feeds['lunar-terms.ics']), 24 * 101)

    def test_apple_language_parameters_folded_titles_and_holiday_labels(self):
        raw = (
            'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nX-WR-CALNAME:中国大陆节假日\r\n'
            'BEGIN:VEVENT\r\nUID:qixi\r\nDTSTART;VALUE=DATE:20260819\r\n'
            'SUMMARY;LANGUAGE=zh_CN:七夕\r\n 节\r\nEND:VEVENT\r\n'
            'BEGIN:VEVENT\r\nUID:labour\r\nDTSTART;VALUE=DATE:20260501\r\n'
            'SUMMARY;LANGUAGE=zh_CN:劳动节（休）\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n'
        ).encode('utf-8')
        reference = apple_reference.parse_reference(raw)
        self.assertEqual(set(reference['covered_names']), {'七夕', '劳动节'})

    def test_new_apple_coverage_is_excluded_without_changing_festival_config(self):
        names = apple_reference.load_covered_names() | {'母亲节'}
        with patch('generate.load_covered_names', return_value=names), tempfile.TemporaryDirectory() as temp:
            feeds = generate.build(2026, 2026, Path(temp))
        self.assertNotIn('母亲节', {e.name for e in feeds['all.ics']})
        self.assertIn('母亲节', {e.name for e in feeds['festival.ics']})

    def test_invalid_or_unavailable_reference_does_not_replace_last_snapshot(self):
        with self.assertRaises(ValueError):
            apple_reference.parse_reference(b'<html>upstream unavailable</html>')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'reference.json'
            path.write_text('last valid snapshot')
            with patch('apple_reference.REFERENCE_PATH', path), patch(
                'apple_reference.urllib.request.urlopen', side_effect=urllib.error.URLError('offline')
            ), self.assertRaises(urllib.error.URLError):
                apple_reference.refresh_reference()
            self.assertEqual(path.read_text(), 'last valid snapshot')

    def test_recorded_coverage_survives_apples_rolling_year_window(self):
        raw = (
            'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nX-WR-CALNAME:中国大陆节假日\r\n'
            'BEGIN:VEVENT\r\nUID:mother\r\nDTSTART;VALUE=DATE:20260510\r\n'
            'SUMMARY:母亲节\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n'
        ).encode('utf-8')
        response = BytesIO(raw)
        response.headers = {}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'reference.json'
            path.write_text(json.dumps({'source_url': apple_reference.SOURCE_URL, 'covered_names': ['妇女节']}))
            with patch('apple_reference.REFERENCE_PATH', path), patch(
                'apple_reference.urllib.request.urlopen', return_value=response
            ):
                apple_reference.refresh_reference()
            self.assertEqual(set(json.loads(path.read_text())['covered_names']), {'妇女节', '母亲节'})
