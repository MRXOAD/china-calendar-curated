from datetime import date
import unittest

import generate


class AnniversaryHistoryTests(unittest.TestCase):
    def test_anniversaries_do_not_predate_their_establishment(self):
        first_years = {
            '中国人民警察节': (2021, 1, 10),
            '全民国家安全教育日': (2016, 4, 15),
            '全国防灾减灾日': (2009, 5, 12),
            '中国医师节': (2018, 8, 19),
            '烈士纪念日': (2014, 9, 30),
            '国家宪法日': (2014, 12, 4),
            '南京大屠杀死难者国家公祭日': (2014, 12, 13),
        }
        events = generate.solar_events(generate.enabled_entries('anniversaries.yaml'), 2000, 2026)
        for name, (year, month, day) in first_years.items():
            with self.subTest(name=name):
                dates = [event.day for event in events if event.name == name]
                self.assertEqual(min(dates), date(year, month, day))
                self.assertIn(date(2026, month, day), dates)
