from __future__ import annotations

import re
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import generate  # noqa: E402


class CalendarGenerationTests(unittest.TestCase):
    def test_lunar_conversion_and_new_years_eve(self) -> None:
        events = generate.lunar_events(generate.enabled_entries("lunar_festivals.yaml"), 2020, 2024)
        dates = {(event.name, event.day) for event in events}
        self.assertIn(("元宵节", date(2020, 2, 8)), dates)
        self.assertIn(("七夕", date(2023, 8, 22)), dates)
        self.assertIn(("重阳节", date(2024, 10, 11)), dates)

    def test_solar_terms(self) -> None:
        terms = generate.solar_terms_for_year(2024)
        self.assertEqual(len(terms), 24)
        self.assertEqual(terms["立春"], date(2024, 2, 4))
        self.assertEqual(terms["春分"], date(2024, 3, 20))
        self.assertEqual(terms["夏至"], date(2024, 6, 21))
        self.assertEqual(terms["秋分"], date(2024, 9, 22))
        self.assertEqual(terms["冬至"], date(2024, 12, 21))

    def test_weekday_rules(self) -> None:
        entries = generate.enabled_entries("international_festivals.yaml")
        events = generate.solar_events(entries, 2024, 2024)
        dates = {event.name: event.day for event in events}
        self.assertEqual(dates["母亲节"], date(2024, 5, 12))
        self.assertEqual(dates["父亲节"], date(2024, 6, 16))
        self.assertEqual(dates["感恩节"], date(2024, 11, 28))

    def test_ics_is_well_formed_and_deduplicated(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            feeds = generate.build(2024, 2025, output)
            for filename, events in feeds.items():
                payload = (output / filename).read_bytes().decode("utf-8")
                self.assertTrue(payload.startswith("BEGIN:VCALENDAR\r\n"))
                self.assertTrue(payload.endswith("END:VCALENDAR\r\n"))
                self.assertEqual(payload.count("BEGIN:VEVENT"), len(events))
                physical_lines = payload.split("\r\n")[:-1]
                self.assertTrue(all(len(line.encode("utf-8")) <= 75 for line in physical_lines), filename)
                self.assertTrue(all(not line.startswith(" ") or index > 0 for index, line in enumerate(physical_lines)), filename)
                uids = re.findall(r"^UID:(.+)\r?$", payload, flags=re.MULTILINE)
                self.assertEqual(len(uids), len(set(uids)), filename)
                starts = re.findall(r"^DTSTART;VALUE=DATE:(\d{8})\r?$", payload, flags=re.MULTILINE)
                self.assertEqual(len(starts), len(events), filename)
                self.assertEqual(len({(event.day, event.name) for event in events}), len(events), filename)
                self.assertNotIn("VALARM", payload)

    def test_uid_is_stable(self) -> None:
        event = generate.Event(date(2027, 10, 17), "重阳节", "double-ninth-festival", "traditional", "农历九月初九")
        self.assertEqual(event.uid, "double-ninth-festival-20271017@china-calendar")

    def test_full_configured_range_has_unique_uids(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            feeds = generate.build(output=Path(temp))
        for filename, events in feeds.items():
            uids = [event.uid for event in events]
            self.assertEqual(len(uids), len(set(uids)), filename)

    def test_apple_statutory_holidays_are_excluded(self) -> None:
        excluded = {"元旦", "春节", "除夕", "清明节", "端午节", "中秋节", "国庆节"}
        with tempfile.TemporaryDirectory() as temp:
            feeds = generate.build(2024, 2025, Path(temp))
        for filename, events in feeds.items():
            self.assertTrue(excluded.isdisjoint(event.name for event in events), filename)


if __name__ == "__main__":
    unittest.main()
