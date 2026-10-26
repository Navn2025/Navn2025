"""Fetch GitHub's public contribution calendar and render a local SVG.

Unknown markup, missing counts and incomplete calendars fail before any output
is replaced. Data is never synthesized. No personal access token is needed.
"""
from datetime import date, datetime, timedelta, timezone
from html import escape
import argparse
import json
from pathlib import Path
import re
import time
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "profile"
COLORS = ["#161b22", "#06452d", "#087443", "#16b86a", "#00ff87"]


def parse_calendar(markup, today=None):
    today = today or datetime.now(timezone.utc).date()
    soup = BeautifulSoup(markup, "html.parser")
    tips = {t.get("for"): t.get_text(" ", strip=True) for t in soup.find_all("tool-tip")}
    days = {}
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        when = date.fromisoformat(cell["data-date"])
        if when > today:
            continue
        raw = cell.get("data-count")
        tooltip = tips.get(cell.get("id"), "")
        if raw is not None and re.fullmatch(r"\d+", raw):
            count = int(raw)
        elif re.match(r"No contributions\b", tooltip, re.I):
            count = 0
        else:
            match = re.match(r"([\d,]+) contributions?\b", tooltip, re.I)
            if not match:
                raise ValueError(f"Cannot read contribution count for {when}: {tooltip!r}")
            count = int(match[1].replace(",", ""))
        level = int(cell["data-level"])
        if not 0 <= level <= 4 or (count == 0) != (level == 0):
            raise ValueError(f"Inconsistent contribution level for {when}")
        item = {"date": when.isoformat(), "count": count, "level": level}
        if when in days and days[when] != item:
            raise ValueError(f"Conflicting calendar cells for {when}")
        days[when] = item
    ordered = [days[k] for k in sorted(days)]
    if len(ordered) < 350:
        raise ValueError(f"Incomplete calendar: {len(ordered)} days")
    if (today-date.fromisoformat(ordered[-1]["date"])).days > 1:
        raise ValueError("GitHub returned an outdated calendar")
    for previous, current in zip(ordered, ordered[1:]):
        if (date.fromisoformat(current["date"])-date.fromisoformat(previous["date"])).days != 1:
            raise ValueError("Calendar contains a missing day")
    return ordered


def statistics(days, today=None):
    today = today or datetime.now(timezone.utc).date()
    longest = run = 0
    for day in days:
        run = run + 1 if day["count"] else 0
        longest = max(longest, run)
    latest = date.fromisoformat(days[-1]["date"])
    index = len(days)-1
    if latest == today and days[index]["count"] == 0:
        index -= 1  # An unfinished UTC day does not break yesterday's streak.
    current = 0
    if latest >= today-timedelta(days=1):
        while index >= 0 and days[index]["count"] > 0:
            current += 1
            index -= 1
    return {"total": sum(d["count"] for d in days), "active_days": sum(d["count"] > 0 for d in days),
            "current_streak": current, "longest_streak": longest,
            "best_day": max(d["count"] for d in days)}


def render(data):
    days, stats = data["days"], data["stats"]
    start = date.fromisoformat(days[0]["date"])
    start -= timedelta(days=(start.weekday()+1) % 7)
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="300" viewBox="0 0 1000 300" '
             'role="img" aria-labelledby="title desc" font-family="Consolas, Liberation Mono, Menlo, monospace">',
             f'<title id="title">{escape(data["username"])} — real GitHub contributions</title>',
             f'<desc id="desc">{stats["total"]} contributions from {days[0]["date"]} to {days[-1]["date"]}. Refreshed {data["generated_at"]}.</desc>',
             '<rect x=".5" y=".5" width="999" height="299" rx="12" fill="#0d1117" stroke="#30363d"/>']

    def text(x, y, content, fill="#8b949e", size=12, extra=""):
        return f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" {extra}>{escape(str(content))}</text>'

    parts += [text(24, 32, "$ git log --contributions --last-year", "#00ff87", 15),
              text(976, 32, "PUBLIC GITHUB CALENDAR", size=10, extra='text-anchor="end"')]
    previous_month = None
    for day in days:
        when = date.fromisoformat(day["date"])
        offset = (when-start).days
        col, row = offset//7, offset % 7
        x, y = 58+col*17, 82+row*17
        # One month label per month, at the first visible week of that month.
        month = (when.year, when.month)
        if month != previous_month:
            next_month_start = (when.replace(day=28)+timedelta(days=4)).replace(day=1)
            # At some year boundaries the initial partial month and the next
            # month share one week column. Prefer the complete month label.
            next_column = (next_month_start-start).days//7
            if col < 52 and (when.day == 1 or next_column > col):
                parts.append(text(x, 67, when.strftime("%b"), size=10))
            previous_month = month
        parts.append(f'<rect x="{x}" y="{y}" width="12" height="12" rx="2" fill="{COLORS[day["level"]]}">'
                     f'<title>{day["date"]}: {day["count"]} contributions</title></rect>')
    for row, name in [(1,"Mon"),(3,"Wed"),(5,"Fri")]:
        parts.append(text(24, 91+row*17, name, size=10))
    parts.append('<path d="M24 216H976" stroke="#21262d"/>')
    for i, (name, value) in enumerate([("CONTRIBUTIONS",stats["total"]),("ACTIVE DAYS",stats["active_days"]),
                                      ("CURRENT STREAK",f'{stats["current_streak"]}d'),("LONGEST STREAK",f'{stats["longest_streak"]}d')]):
        x = 24+i*244
        parts += [text(x, 241, value, "#d7e0e8", 20), text(x+80, 240, name, size=10)]
    parts.append(text(24, 278, f'{days[0]["date"]} to {days[-1]["date"]} / refreshed {data["generated_at"]}', size=10))
    parts.append(text(815, 278, "Less", size=10))
    for i, color in enumerate(COLORS):
        parts.append(f'<rect x="{850+i*17}" y="268" width="12" height="12" rx="2" fill="{color}"/>')
    parts.append(text(940, 278, "More", size=10))
    parts.append('</svg>')
    return "".join(parts)


def fetch(username):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}", username):
        raise ValueError("Invalid GitHub username")
    request = Request(f"https://github.com/users/{username}/contributions",
                      headers={"User-Agent": "Navn2025-profile-art/1.0", "Accept": "text/html"})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8")
        except (OSError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(2**attempt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, help="Parse a saved GitHub response for offline verification")
    args = parser.parse_args()
    config = json.loads((ROOT / "profile" / "config.json").read_text(encoding="utf-8"))
    markup = args.html.read_text(encoding="utf-8") if args.html else fetch(config["username"])
    days = parse_calendar(markup)
    # A date stamp changes once per UTC day, avoiding noisy same-day commits.
    data = {"username": config["username"], "generated_at": datetime.now(timezone.utc).date().isoformat(),
            "stats": statistics(days), "days": days}
    svg = render(data)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, content in [("contributions.json", json.dumps(data, indent=2)+"\n"), ("contributions.svg", svg)]:
        target = OUT / name
        temporary = target.with_suffix(target.suffix+".tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(target)
    print(f'Updated real contributions for {config["username"]}: {data["stats"]}')


if __name__ == "__main__":
    main()
