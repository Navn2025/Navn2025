"""Render daily GitHub stats, primary-language distribution, and weekly activity.

Data comes from GitHub's public API and the real contribution calendar. Language
shares are counts of non-fork repositories by primary language, not code bytes.
"""
from collections import Counter
from datetime import date, timedelta, datetime, timezone
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen
import argparse
import json
import os
import re
import math
from update_contributions import refresh_label

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "profile"
BG, BORDER, INK, MUTED, GREEN = "#0d1117", "#30363d", "#e6edf3", "#8b949e", "#00ff87"
PALETTE = {"Python": "#58a6ff", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
           "Jupyter Notebook": "#da5b0b", "Java": "#b07219", "HTML": "#e34c26", "CSS": "#a78bfa",
           "Kotlin": "#c084fc", "Other": "#6e7681"}


def text(x, y, value, size=13, fill=INK, extra=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" {extra}>{escape(str(value))}</text>'


def svg(w, h, title, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-labelledby="title" font-family="Consolas, Liberation Mono, monospace">'
            f'<title id="title">{escape(title)}</title>{body}</svg>')


def frame(w, h):
    return f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="12" fill="{BG}" stroke="{BORDER}"/>'


def summarize(profile, repos):
    owned = [r for r in repos if not r.get("fork")]
    language_counts = Counter(r["language"] for r in owned if r.get("language"))
    languages = [{"name": name, "count": count} for name, count in language_counts.most_common()]
    return {"public_repos": len(repos), "followers": profile["followers"],
            "stars": sum(r["stargazers_count"] for r in owned), "forks": sum(r["forks_count"] for r in owned),
            "languages": languages, "language_repos": sum(language_counts.values())}


def stats_card(stats, refreshed):
    body = [frame(492,174), text(24,32,"GitHub Stats",17,GREEN), text(468,31,refreshed,10,MUTED,'text-anchor="end"')]
    for i,(name,key) in enumerate([("PUBLIC REPOS","public_repos"),("STARS EARNED","stars"),("FOLLOWERS","followers"),("FORKS EARNED","forks")]):
        x, y = 24+(i%2)*244, 79+(i//2)*64
        body += [text(x,y,stats[key],27),text(x+70,y-2,name,11,MUTED)]
    return "".join(body)


def streak_card(calendar):
    stats = calendar["stats"]
    center = 'text-anchor="middle"'
    body = [frame(492,170), text(24,28,"Contribution Streak",14,GREEN),
            f'<circle cx="246" cy="88" r="42" fill="none" stroke="#16392c" stroke-width="6"/>',
            f'<circle cx="246" cy="88" r="42" fill="none" stroke="{GREEN}" stroke-width="6" stroke-dasharray="190 264" transform="rotate(-90 246 88)"/>']
    body += [text(246,96,stats["current_streak"],28,GREEN,center),text(246,151,"CURRENT / DAYS",11,MUTED,center),
             text(89,95,stats["total"],26,INK,center),text(89,119,"CONTRIBUTIONS",10,MUTED,center),text(89,137,"PAST YEAR",9,MUTED,center),
             text(405,95,stats["longest_streak"],26,INK,center),text(405,119,"LONGEST / DAYS",10,MUTED,center)]
    return "".join(body)


def language_card(stats):
    body = [frame(492,360),text(24,32,"Primary Languages",17,GREEN),text(24,55,"Non-fork repositories by primary language",11,MUTED)]
    languages = list(stats["languages"])
    if len(languages) > 6:
        languages = languages[:5]+[{"name":"Other","count":sum(l["count"] for l in languages[5:])}]
    total = stats["language_repos"]
    circumference, offset = 2*math.pi*65, 0
    body.append('<circle cx="246" cy="148" r="65" fill="none" stroke="#21262d" stroke-width="20"/>')
    for item in languages:
        arc = circumference*item["count"]/total if total else 0
        color = PALETTE.get(item["name"],"#bc8cff")
        body.append(f'<circle cx="246" cy="148" r="65" fill="none" stroke="{color}" stroke-width="20" '
                    f'stroke-dasharray="{max(0,arc-2):.3f} {circumference:.3f}" stroke-dashoffset="{-offset:.3f}" transform="rotate(-90 246 148)">'
                    f'<title>{escape(item["name"])}: {item["count"]} repositories</title></circle>')
        offset += arc
    body += [text(246,149,total,28,INK,'text-anchor="middle"'),text(246,170,"REPOS",10,MUTED,'text-anchor="middle"')]
    for i,item in enumerate(languages):
        x,y = 24+(i%2)*244,258+(i//2)*32
        color = PALETTE.get(item["name"],"#bc8cff")
        share = 100*item["count"]/total if total else 0
        body += [f'<circle cx="{x+4}" cy="{y-4}" r="4" fill="{color}"/>',text(x+17,y,item["name"],11),text(x+210,y,f"{share:.1f}%",11,MUTED,'text-anchor="end"')]
    return "".join(body)


def weekly_values(days):
    weeks = Counter()
    for day in days:
        count = day["count"]
        if not isinstance(count,(int,float)) or not math.isfinite(count) or count < 0:
            raise ValueError("Contribution counts must be finite and nonnegative")
        when = date.fromisoformat(day["date"])
        start = when-timedelta(days=(when.weekday()+1)%7)
        weeks[start] += day["count"]
    return sorted(weeks.items())


def activity_series(days, settings=None):
    settings = settings or {}
    window = settings.get("window_weeks",3)
    percentile = settings.get("cap_percentile",.90)
    minimum, maximum = settings.get("minimum_cap",20),settings.get("maximum_cap",200)
    if not isinstance(window,int) or not 1 <= window <= 12:
        raise ValueError("Activity window must be between 1 and 12 weeks")
    if not .5 <= percentile <= 1 or not 1 <= minimum <= maximum <= 10000:
        raise ValueError("Invalid activity display thresholds")
    weeks = weekly_values(days)
    averages = [sum(value for _,value in weeks[max(0,i-window+1):i+1])/min(i+1,window) for i in range(len(weeks))]
    values = sorted(averages)
    position = (len(values)-1)*percentile
    index = max(0,int(position))
    threshold = (values[index]+(values[min(index+1,len(values)-1)]-values[index])*(position-index)) if values else 0
    cap = min(maximum,max(minimum,math.ceil(threshold/10)*10))
    return weeks,averages,cap,window


def activity_chart(calendar, settings=None):
    weeks,averages,cap,window = activity_series(calendar["days"],settings)
    x0,y0,w,h = 52,63,916,128
    points = [(x0+i*w/max(1,len(weeks)-1),y0+h-min(cap,value)*h/cap) for i,value in enumerate(averages)]
    body = [frame(1000,250),text(24,32,"Contribution Activity",17,GREEN),text(976,31,f"{window}-WEEK AVERAGE / DISPLAY CAP {cap}",10,MUTED,'text-anchor="end"')]
    for ratio in [0,.5,1]:
        y = y0+h-ratio*h
        body += [f'<path d="M{x0} {y}H{x0+w}" stroke="#21262d" stroke-dasharray="3 5"/>',text(x0-10,y+4,round(ratio*cap),10,MUTED,'text-anchor="end"')]
    body.append('<defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#00ff87" stop-opacity=".24"/><stop offset="1" stop-color="#00ff87" stop-opacity="0"/></linearGradient></defs>')
    coords = " ".join(f"{x:.2f},{y:.2f}" for x,y in points)
    body.append(f'<polygon points="{x0},{y0+h} {coords} {x0+w},{y0+h}" fill="url(#area)"/>')
    body.append(f'<polyline points="{coords}" fill="none" stroke="{GREEN}" stroke-width="2.5" stroke-linejoin="round"/>')
    for (x,y),(when,value),average in zip(points,weeks,averages):
        capped = average > cap
        color = "#ffb454" if capped else "#d7fff0"
        body.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{3.5 if capped else 2.6}" fill="{color}"><title>Week of {when}: {value} actual contributions; {window}-week average {average:.1f}'+(f'; display capped at {cap}' if capped else '')+'</title></circle>')
    for i in range(0,len(weeks),5):
        x = points[i][0]
        body.append(text(x,215,weeks[i][0].strftime("%b %d"),10,MUTED,'text-anchor="middle"'))
    body.append(text(24,236,"Smoothed display; amber points exceed the cap. Tooltips retain actual weekly counts.",9,MUTED))
    body.append(text(976,236,f'Refreshed {refresh_label(calendar)}',9,MUTED,'text-anchor="end"'))
    return svg(1000,250,"Navn2025's real weekly contribution activity", "".join(body))


def api(path):
    headers = {"User-Agent":"Navn2025-profile-art", "Accept":"application/vnd.github+json"}
    if os.environ.get("GH_TOKEN"):
        headers["Authorization"] = "Bearer "+os.environ["GH_TOKEN"]
    with urlopen(Request("https://api.github.com/"+path,headers=headers),timeout=30) as response:
        return json.load(response)


def refresh_chart_links(readme, stamp):
    """Change chart image URLs on each fetch so cached READMEs request new art."""
    return re.sub(r'(public/profile/(?:contributions|activity|insights|insights-mobile)\.svg)(?:\?v=[^"\s]+)?',
                  lambda match: match[1]+"?v="+stamp, readme)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline",action="store_true",help="Read saved public API responses in data/")
    args = parser.parse_args()
    config = json.loads((ROOT/"profile/config.json").read_text(encoding="utf-8"))
    user = config["username"]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}",user):
        raise ValueError("Invalid GitHub username")
    if args.offline:
        profile = json.loads((ROOT/"data/github-user.json").read_text(encoding="utf-8-sig"))
        repos = json.loads((ROOT/"data/github-repos.json").read_text(encoding="utf-8-sig"))
    else:
        profile, repos, page = api(f"users/{user}"), [], 1
        while True:
            batch = api(f"users/{user}/repos?per_page=100&type=owner&page={page}")
            repos.extend(batch)
            if len(batch) < 100:
                break
            page += 1
    if len(repos) != profile["public_repos"]:
        raise ValueError("Incomplete public repository response; keep previous charts")
    calendar = json.loads((OUT/"contributions.json").read_text(encoding="utf-8"))
    stats = summarize(profile,repos)
    refreshed = datetime.now(timezone.utc)
    metadata = {"generated_at":refreshed.date().isoformat(),"refreshed_at":refreshed.isoformat(timespec="seconds")}
    stats_body, streak_body, language_body = stats_card(stats,refresh_label(metadata)),streak_card(calendar),language_card(stats)
    combined = stats_body+'<g transform="translate(0 190)">'+streak_body+'</g><g transform="translate(508 0)">'+language_body+'</g>'
    mobile = stats_body+'<g transform="translate(0 190)">'+streak_body+'</g><g transform="translate(0 376)">'+language_body+'</g>'
    files = {"insights.svg":svg(1000,360,"Navn2025's GitHub stats, streaks and primary languages",combined),
             "insights-mobile.svg":svg(492,736,"Navn2025's GitHub insights stacked for mobile",mobile),
             "activity.svg":activity_chart(calendar,config.get("activity_chart")),
             "insights.json":json.dumps({"username":user,**metadata,**stats},indent=2)+"\n"}
    for name,content in files.items():
        target = OUT/name
        temp = target.with_suffix(target.suffix+".tmp")
        temp.write_text(content,encoding="utf-8")
        temp.replace(target)
    readme = ROOT/"README.md"
    readme.write_text(refresh_chart_links(readme.read_text(encoding="utf-8"), refreshed.strftime("%Y%m%dT%H%M%SZ")),encoding="utf-8")
    print(f"Updated GitHub insights: {stats}")


if __name__ == "__main__":
    main()
