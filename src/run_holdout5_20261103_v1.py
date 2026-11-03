"""5차 추가 측정.

흐름: 고정된 공고 6건의 조건을 확정 → 사례별 규칙·진술 대조·조건 판단 → 최종 판단 1회 → 정답과 비교해 저장.
목적: 최종 코드가 4차 24사례 밖의 공고에서 내는 결과를 사례 6개로 본다. 서비스의 공고 대조와 같은 순서다.
결과 해석: 정답은 Codex가 쓴 AI 정답이고 공고들은 이미 측정한 사업의 다른 차수이거나 유사하다. 표본이 작아 정확도 추정치가 아니라 참고 수치다.
"""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
from agents_20261103_v12 import R, prepare_notice, run_final, run_match, run_resolve
from judge_20261102_v6 import judge

OUT = f"{R}/results/holdout5_v1"
os.makedirs(OUT, exist_ok=True)
cases = json.load(open(f"{R}/data/labels/holdout5_cases.json"))["cases"]
SC = {k: tuple(v) for k, v in json.load(open(f"{R}/data/labels/holdout5_scope.json")).items()}


def one(c):
    p = f"{OUT}/{c['id']}.json"
    if os.path.exists(p):
        return json.load(open(p))
    n = c["notice_id"]
    text = open(f"{R}/data/corpus/text/mss_{n}.txt").read()
    ext = prepare_notice(n, text, *SC[n])
    conds, story = ext["conditions"], c["profile"].get("other")
    ans = dict(run_match(conds, c["profile"], story, c["program"]))
    res, _ = run_resolve(conds, {**c["profile"], "answers": ans}, story, text, c["program"])
    ans.update(res)
    prof = {**c["profile"], "answers": ans}
    rule = judge(conds, prof, c["as_of"], c["program"])
    v = run_final(text, SC[n][0], prof, c["as_of"], conds, c["program"])
    out = dict(id=c["id"], notice=n, expected=c["expected"], status=v["status"], rule=rule["status"], period=rule["period_status"], cause=v.get("cause"), reason=v["reason"], ask=v.get("ask", []), gaps=v.get("notice_gaps", []), org=v.get("org_ask", []), verified=v.get("verified"), n_conditions=len(conds))
    json.dump(out, open(p, "w"), ensure_ascii=False, indent=1)
    return out


with ThreadPoolExecutor(6) as ex:
    rows = list(ex.map(one, cases))
summary = dict(n=len(rows), match=sum(r["status"] == r["expected"] for r in rows), false_match=sum(r["expected"] != "일치" and r["status"] == "일치" for r in rows), verified=sum(bool(r["verified"]) for r in rows), rows=[{k: r[k] for k in ("id", "expected", "status", "rule", "cause")} for r in rows])
json.dump(summary, open(f"{OUT}/summary.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(summary, ensure_ascii=False))
for r in rows:
    if r["status"] != r["expected"]:
        print(r["id"], r["expected"], "→", r["status"], r["cause"], r["reason"][:200])
