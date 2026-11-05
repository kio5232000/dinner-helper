#!/usr/bin/env python3
"""Small access probe of three public Tainan-school lunch pages.

No login, access-control bypass, crawl or copying of food photos.
This reports only connectivity and whether previously observed menu names occur.
It does not establish a production API or coverage of all schools.
"""
import datetime
import html
import json
import pathlib
import re
import urllib.error
import urllib.request

DATE = "2026-11-05"
SAMPLES = [
    ("柳營國小", "https://new.lyes.tn.edu.tw/modules/tad_lunch3/index.php?period=" + DATE,
     ["蒜香翅小腿", "蒜香青花菜"]),
    ("勝利國小", "https://web.slps.tn.edu.tw/modules/tad_lunch3/index.php?period=" + DATE,
     ["高昇排骨", "玉米蛋花湯"]),
    ("昭明國中", "https://webold.jmjh.tn.edu.tw/modules/tad_lunch3/index.php?period=" + DATE,
     ["蜂蜜檸檬醬燒豬", "涼拌雲耳"]),
]
results = []
for school, url, expected in SAMPLES:
    item = {"school": school, "url": url, "date": DATE}
    try:
        request = urllib.request.Request(url, headers={
            "User-Agent": "DinnerHelper-public-access-check/1.0",
            "Accept": "text/html",
        })
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read(500000).decode("utf-8", errors="replace")
            item["status"] = response.status
        decoded = html.unescape(raw)
        item["contains_date"] = DATE in decoded
        item["menu_names_found"] = [x for x in expected if x in decoded]
        match_at = decoded.find(expected[0])
        if match_at >= 0:
            item["sample_markup"] = decoded[max(0, match_at-500):match_at+360]
        item["looks_like_lunch_module"] = "tad_lunch3" in raw or "午餐資訊" in decoded
        item["can_read_expected_meals"] = (
            item["status"] == 200 and item["contains_date"]
            and len(item["menu_names_found"]) >= 1
        )
    except urllib.error.HTTPError as error:
        item["status"] = error.code
        item["can_read_expected_meals"] = False
    except Exception as error:
        item["error"] = type(error).__name__
        item["can_read_expected_meals"] = False
    results.append(item)
dest = pathlib.Path("data/tainan-source-probe.json")
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps({
    "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "description": "Limited public-page probe, not an API availability guarantee",
    "results": results
}, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
print(json.dumps(results, ensure_ascii=False, indent=2))
