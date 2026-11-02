"""개발 공고 시험 실행. 흐름: 클린 3차 공고로 총괄 루프 실행 → 정답 라벨과 필드 단위 비교 → 비용 출력. 평가 공고는 쓰지 않는다."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from agents_20261102_v3 import prepare_notice, R
t = time.time()
nid, name, scope, types = sys.argv[1:5]
text = open(f"{R}/data/text/{name}.txt").read()
out = prepare_notice(nid, text, scope, json.loads(types))
json.dump(out, open(f"{R}/results/dev_{nid}.json", "w"), ensure_ascii=False, indent=1)
print("시간", round(time.time() - t), "초, 재추출 포함 추출 횟수", out["rounds"], "미해결", out["unresolved"])
for x in out["trace"]:
    print(x["tool"], json.dumps(x["result"], ensure_ascii=False)[:400])
for c in out["conditions"]:
    print(c["id"], c["kind"], c["field"], c["op"], c["value"], c["group"], c["check"], c["basis"], "|", c["evidence"]["page"], c["evidence"]["quote"][:40], "|", c["exception"])
print("비용 $", round(sum(json.loads(l)["usd"] for l in open(f"{R}/results/usage.jsonl")), 3))
