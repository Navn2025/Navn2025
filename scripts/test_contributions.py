"""Check calendar parsing and streak edge cases without making network calls."""
from datetime import date, timedelta
import unittest

from update_contributions import parse_calendar, render, statistics, refresh_label

TODAY = date(2026, 10, 26)


def calendar(counts=None, missing_tip=None, missing_day=None, future=False):
    counts = counts or {}
    cells, tips = [], []
    for i in range(366 if future else 365):
        when = TODAY-timedelta(days=364-i)
        if when == missing_day:
            continue
        count = counts.get(when, 0)
        cells.append(f'<td class="ContributionCalendar-day" id="d{i}" data-date="{when}" data-level="{1 if count else 0}"></td>')
        if when != missing_tip:
            wording = f"{count:,} contributions" if count else "No contributions"
            tips.append(f'<tool-tip for="d{i}">{wording} on October 26th.</tool-tip>')
    return "".join(cells+tips)


class CalendarTests(unittest.TestCase):
    def test_refresh_time_uses_ist_across_midnight_without_changing_calendar(self):
        days = parse_calendar(calendar({TODAY: 5}), TODAY)
        data = {"username":"Navn2025", "generated_at":str(TODAY),
                "refreshed_at":"2026-10-26T19:15:00+00:00", "days":days,"stats":statistics(days,TODAY)}
        output = render(data)
        self.assertIn("refreshed 2026-10-27 00:45 IST",output)
        self.assertIn("2026-10-26: 5 contributions",output)
        self.assertEqual(days[-1]["date"],str(TODAY))
        self.assertEqual(refresh_label({"generated_at":str(TODAY)}),str(TODAY))

    def test_counts_are_joined_by_id_not_dom_order(self):
        days = parse_calendar(calendar({TODAY: 1234}), TODAY)
        self.assertEqual(len(days), 365)
        self.assertEqual(days[-1]["count"], 1234)
        self.assertEqual(statistics(days, TODAY)["total"], 1234)

    def test_future_calendar_cells_are_excluded(self):
        days = parse_calendar(calendar(future=True), TODAY)
        self.assertEqual(days[-1]["date"], TODAY.isoformat())

    def test_missing_tooltip_does_not_become_zero(self):
        with self.assertRaisesRegex(ValueError, "Cannot read"):
            parse_calendar(calendar(missing_tip=TODAY), TODAY)

    def test_gaps_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing day"):
            parse_calendar(calendar(missing_day=TODAY-timedelta(days=12)), TODAY)

    def test_outdated_response_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "outdated"):
            parse_calendar(calendar(), TODAY+timedelta(days=3))

    def test_empty_response_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            parse_calendar("<html>Rate limited</html>", TODAY)

    def test_empty_today_preserves_yesterday_streak(self):
        counts = {TODAY-timedelta(days=i): 3 for i in [1,2,3]}
        result = statistics(parse_calendar(calendar(counts), TODAY), TODAY)
        self.assertEqual(result["current_streak"], 3)
        self.assertEqual(result["longest_streak"], 3)

    def test_empty_yesterday_breaks_current_streak(self):
        counts = {TODAY-timedelta(days=i): 2 for i in [2,3,4]}
        result = statistics(parse_calendar(calendar(counts), TODAY), TODAY)
        self.assertEqual(result["current_streak"], 0)
        self.assertEqual(result["longest_streak"], 3)

    def test_today_contributes_to_streak_and_svg_escapes_names(self):
        counts = {TODAY-timedelta(days=i): 2 for i in [0,1,2]}
        days = parse_calendar(calendar(counts), TODAY)
        stats = statistics(days, TODAY)
        self.assertEqual(stats["current_streak"], 3)
        svg = render({"username": "name<test>", "generated_at": str(TODAY), "days": days, "stats": stats})
        self.assertIn("name&lt;test&gt;", svg)
        self.assertNotIn("name<test>", svg)
        self.assertIn("6 contributions", svg)


if __name__ == "__main__":
    unittest.main()
