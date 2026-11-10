#!/usr/bin/env python3
"""Import a small allowlisted pilot of public Tainan school lunch pages.

This uses each school's publicly displayed Tad Lunch3 HTML; it does not bypass
the central platform's 403 restrictions. A small list of registry-matched public schools
are used for this pilot. Photos are linked, never copied to our repository.
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import re
import time
import urllib.error
import urllib.request
from bs4 import BeautifulSoup

TZ = datetime.timezone(datetime.timedelta(hours=8))
TODAY = datetime.datetime.now(TZ).date().isoformat()
SCHOOL_REGISTRY = pathlib.Path("data/schools.json")
ROOT = pathlib.Path("data/lunch")

PILOTS = [
    {"name": "柳營國小", "level": "國小", "domain": "new.lyes.tn.edu.tw",
     "url": "https://new.lyes.tn.edu.tw/modules/tad_lunch3/index.php"},
    {"name": "勝利國小", "level": "國小", "district": "東區", "domain": "web.slps.tn.edu.tw",
     "url": "https://web.slps.tn.edu.tw/modules/tad_lunch3/index.php"},
    {"name": "新嘉國小", "level": "國小", "district": "後壁區",
     "url": "https://www2.hces.tn.edu.tw/modules/tad_lunch3/index.php"},
    {"name": "新生國小", "level": "國小", "district": "新營區",
     "url": "https://web.sisps.tn.edu.tw/modules/tad_lunch3/index.php"},
    {"name": "崇明國小", "level": "國小", "district": "東區",
     "url": "https://old.cmes.tn.edu.tw/modules/tad_lunch3/index.php"},
    {"name": "進學國小", "level": "國小", "district": "中西區",
     "url": "https://www.chps.tn.edu.tw/index.php"},
    {"name": "佳興國小", "level": "國小", "district": "佳里區",
     "url": "https://www.jsps.tn.edu.tw/index.php"},
    {"name": "崇明國中", "level": "國中", "district": "東區",
     "url": "https://www.cmjh.tn.edu.tw/index.php"},
    {"name": "紅瓦厝國小", "level": "國小", "district": "歸仁區",
     "url": "https://www.hwces.tn.edu.tw/index.php"},
    {"name": "新南國小", "level": "國小", "district": "安平區",
     "url": "https://www.hnps.tn.edu.tw/index.php"},
    {"name": "新興國小", "level": "國小", "district": "南區",
     "url": "https://www.sses.tn.edu.tw/index.php"},
    {"name": "成功國小", "level": "國小", "district": "中西區",
     "url": "https://www.ckes.tn.edu.tw/index.php"},
    {"name": "大港國小", "level": "國小", "district": "北區",
     "url": "https://www.takes.tn.edu.tw/index.php"},
    {"name": "崑山國小", "level": "國小", "district": "永康區",
     "url": "https://www.kses.tn.edu.tw/index.php"},
    {"name": "楠西國小", "level": "國小", "district": "楠西區",
     "url": "https://www.nsps.tn.edu.tw/index.php"},
    {"name": "大灣國小", "level": "國小", "district": "永康區",
     "url": "https://www.dwps.tn.edu.tw/index.php"},
    {"name": "山上國小", "level": "國小", "district": "山上區",
     "url": "https://www.sases.tn.edu.tw/index.php"},
    {"name": "日新國小", "level": "國小", "district": "南區",
     "url": "https://www.zhes.tn.edu.tw/index.php"},
    {"name": "立人國小", "level": "國小", "district": "北區",
     "url": "https://www.lines.tn.edu.tw/index.php"},
    {"name": "大內國中", "level": "國中", "district": "大內區",
     "url": "https://www.dnjh.tn.edu.tw/index.php"},
    {"name": "新化國中", "level": "國中", "district": "新化區",
     "url": "https://www.shjhs.tn.edu.tw/index.php"},
    {"name": "玉井國中", "level": "國中", "district": "玉井區",
     "url": "https://www.yjjh.tn.edu.tw/index.php"},
    {"name": "大橋國中", "level": "國中", "district": "永康區",
     "url": "https://www.dcjh.tn.edu.tw/index.php"},
    {"name": "大山國小", "level": "國小", "district": "麻豆區",
     "url": "https://dses.dses.tn.edu.tw/index.php"},
    {"name": "關廟國中", "level": "國中", "district": "關廟區",
     "url": "https://www.gmjh.tn.edu.tw/index.php"},
    {"name": "開元國小", "level": "國小", "district": "北區",
     "url": "https://www.kyes.tn.edu.tw/index.php"},
    {"name": "安慶國小", "level": "國小", "district": "安南區",
     "url": "https://schoolweb.tn.edu.tw/~aces_www/index.php"},
]
CATEGORIES = ("主食", "主菜", "副菜", "蔬菜", "湯品", "附餐")

def match_code(rows, expected, level, district=None):
    matches = [
        x for x in rows
        if x.get("city") == "臺南市"
        and x.get("level") == level
        and x.get("name", "").endswith(expected)
        and (not district or x.get("district") == district)
    ]
    if len(matches) != 1:
        raise ValueError(f"Ambiguous pilot school {expected}/{level}: {[x['name'] for x in matches]}")
    return matches[0]


def parse_image_cards(images):
    """Parse dish cards in one verified meal section (never all schools together)."""
    dishes = []
    seen = set()
    for image in images:
        alt = image.get("alt", "").strip()
        if not alt or len(alt) > 65:
            continue
        parent = image.parent
        if parent is None:
            continue
        description = parent.get_text(" ", strip=True)
        category = next((c for c in CATEGORIES if c in description), None)
        if not category:
            continue
        if category == "主食" and any(d["category"] in ("湯品", "附餐") for d in dishes):
            break
        key = (category, alt)
        if key in seen:
            continue
        seen.add(key)
        image_url = image.get("src", "")
        photo_url = image_url if image_url.startswith(
            "https://fatraceschool.k12ea.gov.tw/dish/pic/"
        ) else None
        dishes.append({"name": alt, "category": category, "photo_url": photo_url})
    return dishes[:20]


def parse_tad_page(soup, school, day):
    """Tad Lunch3 full-page template: school/date are in an h3 and date input.

    The module emits a separate top-level h3 for each school, including an
    affiliated kindergarten. Scope dishes to the validated h3 section only.
    The date cannot be taken from form URLs or unrelated page text.
    """
    date_mismatch = False
    for heading in soup.select("h3"):
        title_image = heading.find("img", alt=True)
        if title_image is None:
            continue
        title = re.sub(r"\s+", "", title_image.get("alt", ""))
        if not title.endswith(school + "午餐資訊"):
            continue
        period = heading.select_one('input[name="period"]')
        if period is None:
            continue
        if period.get("value", "").strip() != day:
            date_mismatch = True
            continue
        images = []
        for sibling in heading.next_siblings:
            tag = getattr(sibling, "name", None)
            if tag == "h3":
                break
            if not hasattr(sibling, "select"):
                continue
            images.extend(sibling.select('img[src*="/dish/pic/"]'))
        dishes = parse_image_cards(images)
        if len(dishes) >= 3 and any(d["category"] == "主菜" for d in dishes):
            return dishes
        # A correctly dated heading with no complete meal must not
        # silently use a different school's menu farther down the document.
        raise ValueError("Matching Tad Lunch3 section had no complete menu")
    if date_mismatch:
        raise ValueError("Tad Lunch3 school date input does not match requested day")
    return None

def parse_menu(source_html, school, day):
    soup = BeautifulSoup(source_html, "html.parser")
    validated_tad = parse_tad_page(soup, school, day)
    if validated_tad is not None:
        return validated_tad
    visible = soup.get_text(" ", strip=True)
    # A homepage may IGNORE ?period and display a different day's lunch.
    # Only accept a same-school, same-date lunch heading, not date text
    # elsewhere in the site or a menu for the previous day.
    heading = re.escape(school) + r"\s*" + re.escape(day) + r"\s*午餐\s*資訊"
    match_found = bool(re.search(heading, visible))
    if not match_found:
        # Some Tad Lunch3 templates render the heading SCHOOL NAME inside
        # an <img alt>, with the date in adjacent textual markup.
        # Require a bounded nearby DOM section; unrelated page dates
        # and attached kindergarten sections must never match.
        image_heading = re.compile(re.escape(school) + r"\s*午餐\s*資訊")
        for title_image in soup.select("img[alt]"):
            alt = title_image.get("alt", "")
            if not image_heading.search(alt) or "附設幼兒園" in alt:
                continue
            if day in alt:
                match_found = True
                break
            for ancestor in list(title_image.parents)[:5]:
                local_text = ancestor.get_text(" ", strip=True)
                if day in local_text and len(local_text) <= 1800:
                    match_found = True
                    break
            if match_found:
                break
    if not match_found:
        raise ValueError("No matching school/date lunch heading on this page")
    dishes = parse_image_cards(soup.select('img[src*="/dish/pic/"]'))
    if len(dishes) >= 3 and any(x["category"] == "主菜" for x in dishes):
        return dishes[:20]
    # Homepage lunch blocks often render text but do not include a /dish/pic/
    # image. Only parse a same-school, same-day lunch heading, never generic
    # page text (which could be news, archives or another school's menu).
    lines = [str(t).strip() for t in soup.stripped_strings if str(t).strip()]
    starts = [
        i for i, line in enumerate(lines)
        if day in line and "午餐" in line and "資訊" in line and school in line
    ]
    if not starts:
        raise ValueError("Incomplete menu and no matching dated lunch heading")
    # At most the first lunch section: do not merge attached preschool snacks.
    for start in starts:
        extracted = []
        for i in range(start + 1, min(start + 90, len(lines))):
            line = lines[i]
            if ("校園食材登錄平臺" in line or "重新擷取資料" in line) and extracted:
                break
            if "午餐資訊" in line and day in line and extracted:
                break
            category = next((c for c in CATEGORIES if line == c), None)
            if category is None:
                continue
            if category == "主食" and any(x["category"] in ("湯品", "附餐") for x in extracted):
                break
            if i + 1 >= len(lines):
                continue
            name = lines[i + 1].strip()
            if not name or name in CATEGORIES or len(name) > 65:
                continue
            if any(x["name"] == name and x["category"] == category for x in extracted):
                continue
            extracted.append({"name": name, "category": category, "photo_url": None})
        if len(extracted) >= 3 and any(x["category"] == "主菜" for x in extracted):
            return extracted[:20]
    raise ValueError("Incomplete menu: neither image cards nor dated text lunch block were valid")

MONITOR = pathlib.Path("data/lunch-monitor.json")
REPORT = pathlib.Path("data/tainan-pilot-status.json")

def read_json(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default

def iso_utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")

def utc_day(offset=0):
    return (datetime.datetime.now(TZ).date() + datetime.timedelta(days=offset)).isoformat()

def choose_dates(scope, local_hour):
    if scope == "today":
        return [utc_day()]
    if scope == "tomorrow":
        return [utc_day(1)]
    if scope == "both":
        return [utc_day(), utc_day(1)]
    if local_hour >= 18:
        return [utc_day(1)]
    if local_hour < 8:
        return [utc_day(), utc_day(1)]
    return [utc_day()]

def fingerprint(dishes):
    normalized = [(d["category"], d["name"]) for d in dishes]
    return hashlib.sha256(
        json.dumps(normalized, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

def validated_saved(school, day):
    path = ROOT / school["code"] / (day + ".json")
    value = read_json(path, {}) or {}
    if (value.get("source") == "school_website"
        and value.get("date") == day
        and value.get("school_code") == school["code"]
        and isinstance(value.get("dishes"), list)
        and len(value["dishes"]) >= 3):
        return value
    return None

def sync_school_day(school, entry, day, monitor):
    now = iso_utc()
    code = school["code"]
    key = code + ":" + day
    status = monitor.setdefault(key, {
        "school_code": code, "school_name": school["name"], "date": day,
        "first_checked_at": now, "change_count": 0,
    })
    status["last_checked_at"] = now
    url = entry["url"] + "?period=" + day
    result = {"name": entry["name"], "date": day, "source_url": url,
              "school_code": code}
    old = validated_saved(school, day)
    try:
        request = urllib.request.Request(url, headers={
            "User-Agent": "DinnerHelper-TainanPilot/1.1 (+public informational use)",
            "Accept": "text/html",
        })
        with urllib.request.urlopen(request, timeout=18) as response:
            if response.status != 200:
                raise ValueError(f"HTTP {response.status}")
            markup = response.read(900_000).decode("utf-8", errors="replace")
        dishes = parse_menu(markup, entry["name"], day)
        digest = fingerprint(dishes)
        old_digest = fingerprint(old["dishes"]) if old else None
        first_seen = status.get("first_seen_at") or (
            old.get("first_seen_at") or old.get("retrieved_at") if old else None
        ) or now
        changed = old_digest != digest
        status["first_seen_at"] = first_seen
        if changed:
            status["last_changed_at"] = now
            status["change_count"] = int(status.get("change_count", 0)) + (1 if old else 0)
        if old and not changed:
            result["change"] = "unchanged"
        else:
            output = {
                "source": "school_website",
                "source_url": url,
                "retrieved_at": now,
                "first_seen_at": first_seen,
                "last_changed_at": status.get("last_changed_at", now),
                "revision_count": status["change_count"],
                "menu_fingerprint": digest,
                "date": day, "school_code": code,
                "school_name": school["name"], "dishes": dishes,
            }
            dest = ROOT / code / (day + ".json")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            result["change"] = "updated" if old else "first_seen"
        status["last_status"] = "ok"
        status.pop("last_error", None)
        result["status"] = "ok"
        result["dishes"] = [x["name"] for x in dishes]
        result["first_seen_at"] = first_seen
        result["last_changed_at"] = status.get("last_changed_at")
    except Exception as error:
        status["last_status"] = "unavailable"
        status["last_error"] = f"{type(error).__name__}: {str(error)[:120]}"
        result["status"] = "unavailable"
        result["reason"] = status["last_error"]
        if old:
            result["has_previous_valid_snapshot"] = True
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=["auto","today","tomorrow","both"], default="auto")
    args = parser.parse_args()
    current = datetime.datetime.now(TZ)
    selected_days = choose_dates(args.scope, current.hour)
    registry = read_json(SCHOOL_REGISTRY, {})["schools"]
    schools = [(entry, match_code(
        registry, entry["name"], entry["level"], entry.get("district")
    )) for entry in PILOTS]
    previous = read_json(MONITOR, {}) or {}
    observations = previous.get("observations", {})
    if not isinstance(observations, dict):
        observations = {}
    attempt_results = []
    for day in selected_days:
        for entry, school in schools:
            attempt_results.append(sync_school_day(school, entry, day, observations))
            time.sleep(0.15)

    # Keep monitor compact: only the most recent 21 days.
    oldest = (current.date() - datetime.timedelta(days=21)).isoformat()
    observations = {k:v for k,v in observations.items()
                    if isinstance(v,dict) and v.get("date","") >= oldest}
    MONITOR.write_text(json.dumps({
        "timezone": "Asia/Taipei", "checked_at": iso_utc(),
        "note": "first_seen_at is earliest OUR SYSTEM observed; not the school's publication time",
        "observations": observations
    }, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

    # Compatibility with existing school-selector UI: today's "results".
    # Also expose tomorrow for the future preview selector.
    days = [utc_day(), utc_day(1)]
    by_date = {}
    for day in days:
        records = []
        for entry, school in schools:
            snapshot = validated_saved(school, day)
            found = next((r for r in attempt_results if r["school_code"] == school["code"]
                          and r["date"] == day), None)
            record = {
                "name": entry["name"], "date": day, "school_code": school["code"],
                "status": "ok" if snapshot else "unavailable",
                "source_url": snapshot.get("source_url") if snapshot else entry["url"] + "?period=" + day,
            }
            if found and found.get("reason"):
                record["last_check_note"] = found["reason"]
            if snapshot:
                record["dishes"] = [x["name"] for x in snapshot["dishes"]]
                record["first_seen_at"] = (
                    observations.get(school["code"]+":"+day, {}).get("first_seen_at")
                    or snapshot.get("first_seen_at") or snapshot.get("retrieved_at"))
            records.append(record)
        by_date[day] = records
    REPORT.write_text(json.dumps({
        "checked_at": iso_utc(), "pilot_only": True,
        "checked_dates": selected_days,
        "results": by_date[utc_day()],
        "by_date": by_date,
        "note": "A published menu is not a guarantee the child ate every dish"
    }, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({
        "checked_dates": selected_days,
        "results": [{"school": r["name"], "date":r["date"], "status":r["status"],
                     "change":r.get("change"), "reason":r.get("reason")}
                    for r in attempt_results],
    }, ensure_ascii=False, indent=2))
if __name__ == "__main__":
    main()
