"""판정기-라벨 일관성 검사.

흐름: 정답 조건 라벨을 판정기에 그대로 넣어 42사례를 계산하고 정답과 비교한다.
목적: 추출 오류를 뺀 상태에서 규칙과 라벨이 서로 맞는지 본다. 시스템 성능 지표가 아니다.
결과 해석: 불일치는 판정기 또는 라벨의 오류다. 라벨을 고치면 사유를 기록한다.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from judge_20261102_v2 import judge, validate_graph

L = os.path.expanduser("~/sosang_agent/data/labels")
cases = json.load(open(f"{L}/eval_cases.json"))["cases"]
ok = pok = 0
for c in cases:
    conds = json.load(open(f"{L}/eval_{c['notice_id']}.json"))["conditions"]
    r = judge(conds, c["profile"], c["as_of"], c["program"])
    a = r["status"] == c["expected"]
    b = r["period_status"] == c["period_status"]
    ok += a; pok += b
    miss = [f for f in c["flags"] if f not in r["flags"]]
    if not a or not b or miss or (c["decisive"] and not set(c["decisive"]) & set(r["deciding"])):
        print(c["id"], "정답", c["expected"], c["period_status"], c["decisive"], "| 판정", r["status"], r["period_status"], r["deciding"], "| 빠진 표시", miss)
        print("   ", {k: v for k, v in r["conditions"].items() if v["status"] not in ("일치", "기관 판단")})
print("공고 상태", ok, "/", len(cases), "기간", pok, "/", len(cases))
for n in sorted({c["notice_id"] for c in cases}):
    ok_, errs = validate_graph(json.load(open(f"{L}/eval_{n}.json"))["conditions"], n)
    print(n, ok_, errs[:3])
