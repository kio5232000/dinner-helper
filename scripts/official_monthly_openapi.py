#!/usr/bin/env python3
"""Offline-first caller for the official monthly OpenAPI v1.

Never put accesscodes in GitHub Pages, public repo files or command-line args.
By default NO NETWORK request is sent. Only --send performs a POST and then
only after FATRSCHOOL_OPENAPI_ACCESSCODE is set in the environment.

Swagger v1 has 'consumes': [] (no declared input MIME), so JSON POST is
a tentative implementation requiring authorized live verification.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

BASE = "https://fatraceschool.k12ea.gov.tw/cateringservice/openapi"
SECRET_ENV = "FATRSCHOOL_OPENAPI_ACCESSCODE"
PATHS = {
    "counties": "/county/",
    "datasets": "/opendatadataset/",
    "download": "/opendatadownload/",
}

def build_payload(args, accesscode="<private accesscode>"):
    payload = {"accesscode": accesscode}
    if args.command in {"datasets", "download"}:
        payload.update(year=args.year, month=args.month, county=args.county)
    if args.command == "download":
        payload.update(grade=args.grade, datasetname=args.datasetname)
    return payload

def build_parser():
    p = argparse.ArgumentParser(description="Official monthly OpenAPI v1 request preview")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("counties", help="List official county names")
    ds = sub.add_parser("datasets", help="List datasets for year/month/county")
    dl = sub.add_parser("download", help="Get a dataset CSV download URL")
    for item in (ds, dl):
        item.add_argument("--year", required=True, help="Gregorian year (e.g. 2026)")
        item.add_argument("--month", required=True, help="Two-digit month (e.g. 11)")
        item.add_argument("--county", required=True, help="臺南市")
    dl.add_argument("--grade", required=True, help="Use exact grade returned by datasets")
    dl.add_argument("--datasetname", required=True, help="Use exact datasetname returned by datasets")
    p.add_argument("--send", action="store_true", help="Only send after obtaining a lawful personal accesscode")
    return p

def main():
    args = build_parser().parse_args()
    url = BASE + PATHS[args.command]
    if not args.send:
        print(json.dumps({
            "network_sent": False, "method": "POST", "url": url,
            "example_body": build_payload(args),
            "warning": "Swagger consumes=[]; JSON Content-Type has not been validated live",
        }, ensure_ascii=False, indent=2))
        return 0
    secret = os.getenv(SECRET_ENV, "").strip()
    if not secret:
        print("Missing private environment variable " + SECRET_ENV, file=sys.stderr)
        return 2
    body = json.dumps(build_payload(args, secret), ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Accept": "application/json", "Content-Type": "application/json",
                 "User-Agent": "DinnerHelper-Authorized-OpenAPI-v1/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            result = json.loads(response.read(2000000).decode("utf-8"))
        if not isinstance(result, dict):
            print("Unexpected non-object API response", file=sys.stderr)
            return 1
        # Only display documented response fields; don't print secrets.
        accepted = ("message", "countyList", "datasetList", "link",
                    "year", "month", "county", "grade", "datasetname")
        safe_result = {k: result[k] for k in accepted if k in result}
        print(json.dumps(safe_result, ensure_ascii=False, indent=2))
        return 0
    except urllib.error.HTTPError as exc:
        print("Request failed, HTTP " + str(exc.code) + ". No credentials logged.", file=sys.stderr)
        return 1
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        print("Request failed: " + type(exc).__name__ + ". No credentials logged.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
