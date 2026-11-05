#!/usr/bin/env python3
"""Sync public 114 academic-year elementary school directory (MOE statistics).

This school registry code is NOT equivalent to the lunch-platform SchoolId.
The exported data is only intended for selecting a school.
"""
import datetime
import json
import pathlib
import re
import urllib.request

SOURCE = "https://stats.moe.gov.tw/files/school/114/e1_new.json"
DEST = pathlib.Path("data/schools.json")


def main():
    request = urllib.request.Request(
        SOURCE, headers={"User-Agent": "DinnerHelper/1.2 (public school directory)"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        content = response.read()
    rows = json.loads(content.decode("utf-8-sig"))
    if not isinstance(rows, list) or len(rows) < 1000:
        raise ValueError("School dataset unexpectedly empty or truncated")
    normalized = []
    for row in rows:
        name = str(row.get("學校名稱", "")).strip()
        code = str(row.get("代碼", "")).strip()
        city = re.sub(r"^\[\d+\]", "", str(row.get("縣市名稱", ""))).strip()
        address = re.sub(r"^\[\d+\]", "", str(row.get("地址", ""))).strip()
        if not name or not code or not city:
            continue
        normalized.append({"code": code, "name": name, "city": city, "address": address})
    if len(normalized) < 1000:
        raise ValueError("Insufficient valid school records")
    normalized.sort(key=lambda s: (s["city"], s["name"], s["code"]))
    payload = {
        "academic_year": 114,
        "source": SOURCE,
        "note": "Education statistics school code; not the lunch platform SchoolId",
        "count": len(normalized),
        "schools": normalized,
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Wrote {len(normalized)} schools to {DEST}")


if __name__ == "__main__":
    main()
