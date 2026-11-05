#!/usr/bin/env python3
"""Import a small allowlisted pilot of public Tainan school lunch pages.

This uses each school's publicly displayed Tad Lunch3 HTML; it does not bypass
the central platform's 403 restrictions. Only three manually verified schools
are used for this pilot. Photos are linked, never copied to our repository.
"""
import datetime
import json
import pathlib
import re
import urllib.request
from bs4 import BeautifulSoup

TZ = datetime.timezone(datetime.timedelta(hours=8))
TODAY = datetime.datetime.now(TZ).date().isoformat()
SCHOOL_REGISTRY = pathlib.Path("data/schools.json")
ROOT = pathlib.Path("data/lunch")

PILOTS = [
    {"name": "柳營國小", "level": "國小", "domain": "new.lyes.tn.edu.tw",
     "url": "https://new.lyes.tn.edu.tw/modules/tad_lunch3/index.php"},
    {"name": "勝利國小", "level": "國小", "domain": "web.slps.tn.edu.tw",
     "url": "https://web.slps.tn.edu.tw/modules/tad_lunch3/index.php"},
    {"name": "昭明國中", "level": "國中", "domain": "webold.jmjh.tn.edu.tw",
     "url": "https://webold.jmjh.tn.edu.tw/modules/tad_lunch3/index.php"},
]
CATEGORIES = ("主食", "主菜", "副菜", "蔬菜", "湯品", "附餐")

def match_code(rows, expected, level):
    matches = [
        x for x in rows
        if x.get("city") == "臺南市"
        and x.get("level") == level
        and x.get("name", "").endswith(expected)
    ]
    if len(matches) != 1:
        raise ValueError(f"Ambiguous pilot school {expected}/{level}: {[x['name'] for x in matches]}")
    return matches[0]

def parse_menu(source_html, school, day):
    soup = BeautifulSoup(source_html, "html.parser")
    visible = soup.get_text(" ", strip=True)
    # Require a school/date heading, to avoid importing a stale cached day's menu.
    heading = re.search(re.escape(school) + r".{0,45}" + re.escape(day), visible)
    alternative = re.search(re.escape(day) + r".{0,45}" + re.escape(school), visible)
    if not (heading or alternative):
        raise ValueError("School + target date not found together in visible page")
    dishes = []
    seen = set()
    for image in soup.select('img[src*="/dish/pic/"]'):
        alt = image.get("alt", "").strip()
        if not alt or len(alt) > 65:
            continue
        parent = image.parent
        if not parent:
            continue
        description = parent.get_text(" ", strip=True)
        category = next((c for c in CATEGORIES if re.search(r"(?<!\\w)" + c, description)), None)
        if category is None:
            category = next((c for c in CATEGORIES if c in description), None)
        if not category:
            continue
        key = (category, alt)
        if key in seen:
            continue
        seen.add(key)
        image_url = image.get("src", "")
        # A source photo might be blocked or unlicensed for copying.
        # Store only source references; our UI will fall back to SVG when needed.
        photo_url = image_url if image_url.startswith("https://fatraceschool.k12ea.gov.tw/dish/pic/") else None
        dishes.append({"name": alt, "category": category, "photo_url": photo_url})
    if len(dishes) < 3 or not any(x["category"] == "主菜" for x in dishes):
        raise ValueError("Incomplete menu: no main dish or fewer than three courses")
    return dishes[:20]

def main():
    registry = json.loads(SCHOOL_REGISTRY.read_text(encoding="utf-8"))["schools"]
    summary = []
    for entry in PILOTS:
        school = match_code(registry, entry["name"], entry["level"])
        url = entry["url"] + "?period=" + TODAY
        request = urllib.request.Request(url, headers={
            "User-Agent": "DinnerHelper-Pilot/1.0 (public school lunch page)",
            "Accept": "text/html",
        })
        result = {"name": entry["name"], "date": TODAY, "source_url": url}
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                if response.status != 200:
                    raise ValueError(f"HTTP {response.status}")
                markup = response.read(1_000_000).decode("utf-8", errors="replace")
            dishes = parse_menu(markup, entry["name"], TODAY)
            output = {
                "source": "school_website",
                "source_url": url,
                "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "date": TODAY,
                "school_code": school["code"],
                "school_name": school["name"],
                "dishes": dishes,
            }
            dest = ROOT / school["code"] / (TODAY + ".json")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            result["status"] = "ok"
            result["school_code"] = school["code"]
            result["dishes"] = [x["name"] for x in dishes]
        except Exception as error:
            result["status"] = "unavailable"
            result["reason"] = f"{type(error).__name__}: {str(error)[:100]}"
        summary.append(result)
    report = pathlib.Path("data/tainan-pilot-status.json")
    report.write_text(json.dumps({
        "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "pilot_only": True,
        "results": summary
    }, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
