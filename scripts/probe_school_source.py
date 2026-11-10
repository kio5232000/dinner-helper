#!/usr/bin/env python3
"""Read-only checker for a candidate Tainan public school's lunch URL.

The command does NOT add any school to PILOTS or write lunch data.
Usage:
python -m scripts.probe_school_source --school 新興國小 --level 國小 \
  --district 南區 --url https://www.sses.tn.edu.tw/index.php --date 2026-11-10
"""
import argparse
import datetime
import json
import pathlib
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
from scripts.import_tainan_pilot import match_code, parse_menu, TZ

def inspect(school, level, district, url, day, registry, opener=urllib.request.urlopen):
    result={"school":school, "level":level, "district":district, "date":day,
            "source_url":url, "status":"unavailable"}
    parsed=urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not (parsed.hostname and parsed.hostname.endswith(".tn.edu.tw")):
        result["reason"]="Only verified public HTTPS .tn.edu.tw sources can be tested"
        return result
    try:
        normalized=datetime.date.fromisoformat(day).isoformat()
        if day != normalized:
            raise ValueError("Invalid ISO date")
        match=match_code(registry,school,level,district)
        result["school_code"]=match["code"]
        if parsed.path.endswith("/"):
            base=url.rstrip("/")+"/index.php"
        else:
            base=url
        joiner="&" if urllib.parse.urlsplit(base).query else "?"
        target=base+joiner+urllib.parse.urlencode({"period":day})
        req=urllib.request.Request(target,headers={
            "User-Agent":"DinnerHelper-TainanSchoolChecker/1.0 (public page verification)",
            "Accept":"text/html"
        })
        with opener(req, timeout=18) as response:
            if response.status!=200:
                raise ValueError("HTTP "+str(response.status))
            final=urllib.parse.urlsplit(response.geturl())
            if final.hostname and not final.hostname.endswith(".tn.edu.tw"):
                raise ValueError("School page redirected out of .tn.edu.tw")
            html=response.read(900000).decode("utf-8",errors="replace")
        soup=BeautifulSoup(html,"html.parser")
        dishes=parse_menu(html,school,day)
        result["status"]="ok"
        result["fetch_url"]=target
        result["dishes"]=[{"category":d["category"],"name":d["name"]} for d in dishes]
        result["format"]="tad_lunch3" if soup.select_one('input[name="period"]') else "school_homepage"
        result["note"]="Read-only validation; does not imply permission for future crawling or image reuse"
    except Exception as exc:
        result["reason"]=type(exc).__name__+": "+str(exc)[:140]
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--school",required=True)
    parser.add_argument("--district",required=True)
    parser.add_argument("--level",choices=["國小","國中"],required=True)
    parser.add_argument("--url",required=True)
    parser.add_argument("--date",default=datetime.datetime.now(TZ).date().isoformat())
    args=parser.parse_args()
    registry=json.loads(pathlib.Path("data/schools.json").read_text(encoding="utf-8"))["schools"]
    result=inspect(args.school,args.level,args.district,args.url,args.date,registry)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result["status"]=="ok" else 1

if __name__=="__main__":
    raise SystemExit(main())
