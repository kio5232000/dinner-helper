#!/usr/bin/env python3
"""Probe publicly documented school lunch access without bypassing restrictions.

Writes only HTTP status + CORS diagnostics; no meal data is redistributed.
The historical offered/meal URL is not asserted to be supported in 2026.
"""
import datetime
import json
import pathlib
import urllib.error
import urllib.request

BASE = "https://fatraceschool.k12ea.gov.tw"
TEST_DATE = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).date().isoformat()
TARGETS = {
    "search_page": BASE + "/frontend/search.html",
    "openapi": BASE + "/cateringservice/web/openapi_doc/v1/openapi.json",
    "historical_meal_example": BASE + "/offered/meal?KitchenId=all&MenuType=1&period=" + TEST_DATE + "&SchoolId=64643",
}
output = {"checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "note": "Access tests from GitHub-hosted runner; results may differ for visitors.", "results": {}}
for label, url in TARGETS.items():
    req = urllib.request.Request(url, headers={
        "User-Agent": "DinnerHelper/1.2 public endpoint compatibility probe",
        "Origin": "https://kio5232000.github.io",
        "Accept": "application/json,text/html;q=0.9,*/*;q=0.5"
    })
    try:
        with urllib.request.urlopen(req, timeout=12) as res:
            payload = res.read(1024 * 120)
            status = res.status
            headers = res.headers
    except urllib.error.HTTPError as e:
        payload = e.read(1024)
        status = e.code
        headers = e.headers
    except Exception as e:
        output["results"][label] = {"status": "network_error", "reason": type(e).__name__}
        continue
    origin = headers.get("Access-Control-Allow-Origin")
    entry = {
        "status": status,
        "content_type": headers.get("Content-Type"),
        "access_control_allow_origin": origin,
        "browser_cors_ok": origin in ("*", "https://kio5232000.github.io"),
    }
    if label != "search_page" and status == 200:
        try:
            document=json.loads(payload)
            entry["json_type"]=type(document).__name__
            if isinstance(document, dict):
                entry["top_keys"]=list(document.keys())[:12]
        except (json.JSONDecodeError, UnicodeDecodeError):
            entry["json_type"]="not_json_or_truncated"
    output["results"][label] = entry
dest=pathlib.Path("data/source-diagnostics.json")
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(output, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps(output,ensure_ascii=False,indent=2))
