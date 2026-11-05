import json
from pathlib import Path
from collections import Counter
data=json.loads(Path("data/schools.json").read_text(encoding="utf-8"))
schools=data["schools"]
counts=Counter(s.get("level","國小") for s in schools)
summary={
 "total":len(schools),
 "by_level":dict(counts),
 "with_district":sum(bool(s.get("district")) for s in schools),
 "tainan_yongkang":sum(s.get("city")=="臺南市" and s.get("district")=="永康區" for s in schools)
}
Path("data/school-stats.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(summary)
