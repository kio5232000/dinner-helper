#!/usr/bin/env python3
"""Diagnostic only: identify why validated lunch cards fail at a school.
Run only on approved public school pages. Print minimal lunch-related markers.
Never store scraped HTML or request any protected API.
"""
import datetime
import json
import re
import urllib.request
from bs4 import BeautifulSoup
from scripts.import_tainan_pilot import PILOTS, TZ

NEEDED = {"勝利國小", "新生國小", "崇明國小", "柳營國小"}
day = datetime.datetime.now(TZ).date().isoformat()
for school in (s for s in PILOTS if s["name"] in NEEDED):
    url=school["url"]+"?period="+day
    result={"school":school["name"],"requested_day":day}
    try:
        request=urllib.request.Request(url,headers={"User-Agent":"DinnerHelper-TainanPilot/1.1 (school lunch diagnostic)","Accept":"text/html"})
        with urllib.request.urlopen(request,timeout=18) as res:
            text=res.read(900000).decode("utf-8",errors="replace")
            result["status"]=res.status
            result["final_url"]=res.url
        soup=BeautifulSoup(text,"html.parser")
        result["html_bytes"]=len(text)
        result["title"]=(soup.title.get_text(" ",strip=True)[:120] if soup.title else "")
        result["requested_day_count"]=text.count(day)
        result["image_dish_count"]=len(soup.select('img[src*="/dish/pic/"]'))
        result["title_image_alts"]=[x.get("alt","")[:90] for x in soup.select("img[alt]") if any(w in x.get("alt","") for w in ("午餐","食材","菜色"))][:8]
        lines=[s.strip() for s in soup.stripped_strings if s.strip()]
        result["lunch_lines"]=[{"index":i,"text":x[:160]} for i,x in enumerate(lines) if ("午餐" in x or day in x)][:18]
        result["snippet"]=[]
        for m in list(re.finditer(re.escape(day),text))[:3]:
            frag=re.sub(r"<[^>]+>"," ",text[max(0,m.start()-120):min(len(text),m.end()+170)])
            result["snippet"].append(re.sub(r"\s+"," ",frag).strip()[:240])
    except Exception as error:
        result["error"]=type(error).__name__+": "+str(error)[:160]
    print(json.dumps(result,ensure_ascii=False))
