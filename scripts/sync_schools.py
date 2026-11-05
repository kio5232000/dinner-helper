#!/usr/bin/env python3
"""Build a school selector from official MOE elementary and junior-high directories.

The directory's school code is NOT guaranteed to match the school lunch
platform's SchoolId. This file is ONLY for school selection.
"""
import json
import pathlib
import re
import urllib.request

SOURCES = [
    ("國小", "https://stats.moe.gov.tw/files/school/114/e1_new.json", 1000),
    ("國中", "https://stats.moe.gov.tw/files/opendata/j1_new.json", 400),
]
DEST = pathlib.Path("data/schools.json")


def canonical(value):
    return str(value or "").strip().replace("台", "臺")


def district_from_address(address, city):
    """Find the first administrative district after the city/county prefix."""
    normalized = canonical(re.sub(r"^\[\d+\]|^\d{3,6}", "", address))
    normalized_city = canonical(city)
    if normalized.startswith(normalized_city):
        remaining = normalized[len(normalized_city):]
    else:
        i = normalized.find(normalized_city)
        remaining = normalized[i + len(normalized_city):] if i >= 0 else normalized
    # The district suffix ends at 區／鄉／鎮／市; no inferred district if unknown.
    match = re.match(r"^(.{1,6}?(?:區|鄉|鎮|市))", remaining)
    return match.group(1) if match else ""


def fetch_rows(url, min_rows):
    request = urllib.request.Request(url, headers={
        "User-Agent": "DinnerHelper/1.4 (MOE public school directory)"
    })
    with urllib.request.urlopen(request, timeout=35) as response:
        rows = json.loads(response.read().decode("utf-8-sig"))
    if not isinstance(rows, list) or len(rows) < min_rows:
        raise ValueError(f"School dataset unexpected format or insufficient records: {url}")
    return rows


def main():
    records = []
    counts = {}
    for level, url, minimum in SOURCES:
        rows = fetch_rows(url, minimum)
        count = 0
        for row in rows:
            if not isinstance(row, dict):
                continue
            name = str(row.get("學校名稱", "")).strip()
            code = str(row.get("代碼", "")).strip()
            city = re.sub(r"^\[\d+\]", "", str(row.get("縣市名稱", ""))).strip()
            address = re.sub(r"^\[\d+\]", "", str(row.get("地址", ""))).strip()
            if not (name and code and city):
                continue
            records.append({
                "code": code,
                "name": name,
                "city": city,
                "district": district_from_address(address, city),
                "level": level,
                "address": address,
            })
            count += 1
        if count < minimum:
            raise ValueError(f"Insufficient valid records for {level}: {count}")
        counts[level] = count
    records.sort(key=lambda s: (
        canonical(s["city"]), canonical(s["district"]),
        0 if s["level"] == "國小" else 1, s["name"], s["code"]
    ))
    payload = {
        "academic_year": 114,
        "sources": {level: url for level, url, _ in SOURCES},
        "note": "MOE directory codes are not confirmed lunch-platform SchoolIds",
        "count": len(records),
        "counts_by_level": counts,
        "schools": records,
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(records)} schools {counts} to {DEST}")


if __name__ == "__main__":
    main()
