#!/usr/bin/env python3
"""Produce a transparent rolling report for the Tainan school lunch pilot.

The metrics are based on observed school/day records, not promises of
real-time upstream publication. Missing meals can include school holidays.
"""
import datetime
import json
import pathlib
from scripts.import_tainan_pilot import TZ, MONITOR, REPORT, ROOT, PILOTS, read_json, match_code

OUT=pathlib.Path("data/coverage-summary.json")
REGISTRY=pathlib.Path("data/schools.json")

def build_summary(registry, report, monitor, today):
    candidates=[]
    for p in PILOTS:
        try:
            s=match_code(registry,p["name"],p["level"],p.get("district"))
            candidates.append({"name":p["name"],"district":s["district"],"level":s["level"],"code":s["code"]})
        except ValueError:
            # The importer should separately report registry errors.
            continue
    codes={x["code"] for x in candidates}
    by_date=report.get("by_date",{})
    status={}
    for day in [today.isoformat(), (today+datetime.timedelta(days=1)).isoformat()]:
        entries=by_date.get(day,[])
        good=[x for x in entries if x.get("status")=="ok" and x.get("school_code") in codes and x.get("date")==day]
        status[day]={
            "school_count":len(entries),
            "available":len(good),
            "unavailable":max(0,len(entries)-len(good)),
            "available_codes":[x["school_code"] for x in good],
            "checked_for_date":day in report.get("checked_dates",[]),
        }
    obs=monitor.get("observations",{})
    day_rows=[]
    for delta in range(6,-1,-1):
        day=today-datetime.timedelta(days=delta)
        if day.weekday()>4:
            continue
        key=day.isoformat()
        observed=[v for v in obs.values() if isinstance(v,dict) and
                  v.get("date")==key and v.get("school_code") in codes]
        with_dishes=[v for v in observed if v.get("first_seen_at")]
        day_rows.append({
            "date":key, "observed_schools":len(observed),
            "schools_with_menu_observed":len(with_dishes),
            "observation_rate_percent":(
                round(100*len(with_dishes)/len(observed),1) if observed else None
            ),
            "last_observed_change_count":sum(int(v.get("change_count",0)) for v in observed),
            "note":"Observed coverage only; not school-wide publishing reliability or attendance"
        })
    by_school=[]
    for school in candidates:
        school_obs=[v for v in obs.values() if isinstance(v,dict) and
                    v.get("school_code")==school["code"] and
                    today-datetime.timedelta(days=6)<=datetime.date.fromisoformat(v["date"])<=today and
                    datetime.date.fromisoformat(v["date"]).weekday()<5]
        seen=sum(1 for row in school_obs if row.get("first_seen_at"))
        by_school.append({
            **school, "observed_school_days":len(school_obs),
            "menu_observed_days":seen,
            "observed_rate_percent":round(seen/len(school_obs)*100,1) if school_obs else None,
        })
    return {
        "timezone":"Asia/Taipei",
        "generated_at":datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "target_date":today.isoformat(),
        "pilot_schools":len(candidates),
        "current_and_next":status,
        "recent_school_days":day_rows,
        "by_school":by_school,
        "limitations":"Rates only indicate menus our system observed for checked school-days; they do not prove publication times or meals served. School closures and late publication may lower the rate."
    }

def main():
    registry=read_json(REGISTRY,{}).get("schools",[])
    report=read_json(REPORT,{})
    monitor=read_json(MONITOR,{})
    today=datetime.datetime.now(TZ).date()
    summary=build_summary(registry,report,monitor,today)
    OUT.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"pilot_schools":summary["pilot_schools"],"current_and_next":summary["current_and_next"]},ensure_ascii=False))
if __name__=="__main__":
    main()
