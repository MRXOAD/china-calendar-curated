#!/usr/bin/env python3
"""Generate curated China Calendar iCalendar feeds from YAML configuration."""

from __future__ import annotations

import argparse
import calendar as month_calendar
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml
from lunar_python import Lunar, LunarYear, Solar


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DIST_DIR = ROOT / "dist"
TERM_NAMES = (
    "立春", "雨水", "惊蛰", "春分", "清明", "谷雨", "立夏", "小满", "芒种", "夏至", "小暑", "大暑",
    "立秋", "处暑", "白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪", "冬至", "小寒", "大寒",
)
WEEKDAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
SAFE_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")


@dataclass(frozen=True, order=True)
class Event:
    day: date
    name: str
    slug: str
    category: str
    description: str

    @property
    def uid(self) -> str:
        # A Gregorian year alone collides when one lunar festival occurs both
        # in January and December of that year (for example 腊八节).
        return f"{self.slug}-{self.day:%Y%m%d}@china-calendar"


def read_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def enabled_entries(filename: str) -> list[dict[str, Any]]:
    entries = read_yaml(DATA_DIR / filename)
    if not isinstance(entries, list):
        raise ValueError(f"{filename} must contain a YAML list")
    result = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError(f"{filename} contains a non-mapping entry")
        if entry.get("enabled", True):
            validate_entry(entry, filename)
            result.append(entry)
    return result


def validate_entry(entry: dict[str, Any], filename: str) -> None:
    for key in ("name", "slug", "type", "category", "description"):
        if not isinstance(entry.get(key), str) or not entry[key]:
            raise ValueError(f"{filename}: {key} is required")
    if not SAFE_SLUG.fullmatch(entry["slug"]):
        raise ValueError(f"{filename}: invalid slug {entry['slug']!r}")
    if "start_year" in entry and (type(entry["start_year"]) is not int or not 1 <= entry["start_year"] <= 9999):
        raise ValueError(f"{filename}: start_year must be an integer from 1 to 9999")


def nth_weekday(year: int, month: int, weekday: str, nth: int) -> date:
    target = WEEKDAYS[weekday]
    first_weekday, days = month_calendar.monthrange(year, month)
    day = 1 + (target - first_weekday) % 7 + (nth - 1) * 7
    if day > days:
        raise ValueError(f"{year}-{month} has no {nth}th {weekday}")
    return date(year, month, day)


def solar_events(entries: Iterable[dict[str, Any]], start: int, end: int) -> list[Event]:
    events: list[Event] = []
    for year in range(start, end + 1):
        for entry in entries:
            if year < entry.get("start_year", 1):
                continue
            kind = entry["type"]
            if kind == "solar":
                event_date = date(year, int(entry["month"]), int(entry["day"]))
            elif kind == "weekday":
                event_date = nth_weekday(year, int(entry["month"]), entry["weekday"], int(entry["nth"]))
            else:
                continue
            events.append(Event(event_date, entry["name"], entry["slug"], entry["category"], entry["description"]))
    return events


def solar_terms_for_year(year: int) -> dict[str, date]:
    table = Solar.fromYmd(year, 6, 1).getLunar().getJieQiTable()
    terms: dict[str, date] = {}
    for term in TERM_NAMES:
        # The upstream table uses the Chinese key for the preceding winter
        # solstice and DONG_ZHI for the one in the current Gregorian year.
        solar = table["DONG_ZHI" if term == "冬至" else term]
        event_date = date(solar.getYear(), solar.getMonth(), solar.getDay())
        if event_date.year == year:
            terms[term] = event_date
    if set(terms) != set(TERM_NAMES):
        missing = sorted(set(TERM_NAMES) - set(terms))
        raise ValueError(f"solar-term calculation incomplete for {year}: {missing}")
    return terms


def lunar_events(entries: Iterable[dict[str, Any]], start: int, end: int) -> list[Event]:
    events: list[Event] = []
    for lunar_year in range(start - 1, end + 1):
        terms = solar_terms_for_year(lunar_year)
        for entry in entries:
            kind = entry["type"]
            if kind == "lunar":
                solar = Lunar.fromYmd(lunar_year, int(entry["month"]), int(entry["day"])).getSolar()
                event_date = date(solar.getYear(), solar.getMonth(), solar.getDay())
            elif kind == "lunar_new_year_eve":
                last_day = LunarYear.fromYear(lunar_year).getMonth(12).getDayCount()
                solar = Lunar.fromYmd(lunar_year, 12, last_day).getSolar()
                event_date = date(solar.getYear(), solar.getMonth(), solar.getDay())
            elif kind == "solar_term_festival":
                event_date = terms[entry["term"]]
            else:
                continue
            if start <= event_date.year <= end:
                events.append(Event(event_date, entry["name"], entry["slug"], entry["category"], entry["description"]))
    return events


def term_events(start: int, end: int) -> list[Event]:
    events: list[Event] = []
    for year in range(start, end + 1):
        for term, event_date in solar_terms_for_year(year).items():
            events.append(Event(event_date, term, f"solar-term-{TERM_SLUGS[term]}", "solar_term", "二十四节气"))
    return events


TERM_SLUGS = {
    "立春": "lichun", "雨水": "yushui", "惊蛰": "jingzhe", "春分": "chunfen", "清明": "qingming", "谷雨": "guyu",
    "立夏": "lixia", "小满": "xiaoman", "芒种": "mangzhong", "夏至": "xiazhi", "小暑": "xiaoshu", "大暑": "dashu",
    "立秋": "liqiu", "处暑": "chushu", "白露": "bailu", "秋分": "qiufen", "寒露": "hanlu", "霜降": "shuangjiang",
    "立冬": "lidong", "小雪": "xiaoxue", "大雪": "daxue", "冬至": "dongzhi", "小寒": "xiaohan", "大寒": "dahan",
}


def unique(events: Iterable[Event]) -> list[Event]:
    seen: set[tuple[date, str]] = set()
    result: list[Event] = []
    for event in sorted(events):
        key = (event.day, event.name)
        if key not in seen:
            seen.add(key)
            result.append(event)
    return result


def escape_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def fold_ical_line(line: str) -> list[str]:
    raw = line.encode("utf-8")
    lines: list[bytes] = []
    first = True
    while raw:
        limit = 75 if first else 74
        chunk = raw[:limit]
        while len(chunk) < len(raw) and (raw[len(chunk)] & 0xC0) == 0x80:
            chunk = chunk[:-1]
        lines.append((b"" if first else b" ") + chunk)
        raw = raw[len(chunk):]
        first = False
    return [item.decode("utf-8") for item in lines]


def render_calendar(events: Iterable[Event], name: str, config: dict[str, Any], stamp: str) -> str:
    lines = [
        "BEGIN:VCALENDAR", f"PRODID:{config['prodid']}", "VERSION:2.0", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
        f"X-WR-CALNAME:{escape_text(name)}", f"X-WR-TIMEZONE:{config['timezone']}",
    ]
    for event in unique(events):
        lines.extend((
            "BEGIN:VEVENT", f"UID:{event.uid}", f"DTSTAMP:{stamp}", f"DTSTART;VALUE=DATE:{event.day:%Y%m%d}",
            f"SUMMARY:{escape_text(event.name)}", f"DESCRIPTION:{escape_text(event.description)}", "TRANSP:TRANSPARENT", "END:VEVENT",
        ))
    lines.append("END:VCALENDAR")
    return "\r\n".join(part for line in lines for part in fold_ical_line(line)) + "\r\n"


def build(start: int | None = None, end: int | None = None, output: Path = DIST_DIR) -> dict[str, list[Event]]:
    config = read_yaml(DATA_DIR / "calendar.yaml")
    start = int(start or config["start_year"])
    end = int(end or config["end_year"])
    if start > end:
        raise ValueError("start year must not be after end year")
    solar = solar_events(
        enabled_entries("solar_festivals.yaml") + enabled_entries("international_festivals.yaml") + enabled_entries("anniversaries.yaml") + enabled_entries("culture_festivals.yaml"), start, end,
    )
    traditional = lunar_events(enabled_entries("lunar_festivals.yaml"), start, end)
    terms = term_events(start, end)
    feeds = {
        "festival.ics": unique(solar + traditional),
        "lunar.ics": unique(traditional + terms),
        "lunar-terms.ics": unique(terms),
        "all.ics": unique(solar + traditional + terms),
    }
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    names = {"festival.ics": "精选节日与纪念日", "lunar.ics": "农历传统节日与二十四节气", "lunar-terms.ics": "二十四节气", "all.ics": "精选中国节日、农历与二十四节气"}
    for filename, events in feeds.items():
        (output / filename).write_text(render_calendar(events, names[filename], config, stamp), encoding="utf-8", newline="")
    return feeds


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-year", type=int)
    parser.add_argument("--end-year", type=int)
    parser.add_argument("--output", type=Path, default=DIST_DIR)
    args = parser.parse_args()
    feeds = build(args.start_year, args.end_year, args.output)
    print("Generated " + ", ".join(f"{name} ({len(events)} events)" for name, events in feeds.items()))


if __name__ == "__main__":
    main()
