"""최종 판단 평가 스크립트.

흐름: 저장된 조건·진술 대조·조건 판단을 불러옴 → 규칙 결과 계산 → 최종 판단 에이전트 실행(반복 가능) → 정답과 비교해 비교군 표 저장.
목적: 공고 전체를 읽는 최종 판단이 틀린 일치와 오답을 얼마나 줄이는지 같은 사례로 잰다.
결과 해석: 이미 오답을 본 공고에서는 사후 수치다. 코드 고정 뒤 처음 재는 공고에서만 주 수치로 쓴다. 정답은 AI 초안이다.
사용법: python run_final.py <결과폴더> <라벨접두어> <반복수>
"""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
from agents_round4 import R, run_final
from judge_round import judge

OUT, PRE, REP = f"{R}/results/{sys.argv[1]}", sys.argv[2], int(sys.argv[3])
L = f"{R}/data/labels"
SC = {k: tuple(v) for k, v in json.load(open(f"{L}/{PRE}_scope.json")).items()}
cases = [c for c in json.load(open(f"{L}/{PRE}_cases.json"))["cases"] if c["notice_id"] in SC]
gold = {n: json.load(open(f"{L}/{PRE}_{n}.json")) for n in SC}
text = {n: open(f"{R}/data/text/{gold[n]['source_text']}.txt").read() for n in SC}
ext = {n: json.load(open(f"{OUT}/extract_{n}.json")) for n in SC}
prev = json.load(open(f"{OUT}/results.json"))


def full_profile(c):
    ans = {}
    for name in (f"match_A_{c['id']}_r0.json", f"resolve_{c['id']}_r0.json"):
        p = f"{OUT}/{name}"
        if os.path.exists(p):
            d = json.load(open(p))
            ans.update(d.get("answers", d) if name.startswith("resolve") else d)
    return {**c["profile"], "answers": ans}


def one(job):
    c, r = job
    p = f"{OUT}/final_{c['id']}_r{r}.json"
    if os.path.exists(p):
        return json.load(open(p))
    n = c["notice_id"]
    prof = full_profile(c)
    # 설명 문장(other)도 사업체 정보로 함께 넘긴다.
    v = run_final(text[n], SC[n][0], prof, c["as_of"], ext[n]["conditions"], c["program"])
    json.dump(v, open(p, "w"), ensure_ascii=False)
    return v


jobs = [(c, r) for c in cases for r in range(REP)]
with ThreadPoolExecutor(6) as ex:
    done = list(ex.map(one, jobs))
F = {(j[0]["id"], j[1]): d for j, d in zip(jobs, done)}
arms = {k: (lambda c, k=k: prev["cases"][c["id"]][k]["status"]) for k in next(iter(prev["cases"].values()))}
arms["F"] = lambda c: F[(c["id"], 0)]["status"]
scores = {}
for k, f in arms.items():
    ask = [c for c in cases if c["expected"] == "확인 필요"]
    scores[k] = dict(status_match=sum(f(c) == c["expected"] for c in cases), n=len(cases), false_match=sum(c["expected"] != "일치" and f(c) == "일치" for c in cases), ask_recall=f"{sum(f(c) == '확인 필요' for c in ask)}/{len(ask)}", wrong=[f"{c['id']}:{c['expected']}→{f(c)}" for c in cases if f(c) != c["expected"]])
unstable = [c["id"] for c in cases if REP > 1 and len({F[(c["id"], r)]["status"] for r in range(REP)}) > 1]
unverified = sum(not v.get("verified") for v in done)
out = dict(scores=scores, final_unstable=unstable, repeat=REP, unverified_quotes=unverified)
json.dump(out, open(f"{OUT}/final_scores.json", "w"), ensure_ascii=False, indent=1)
for k in ("A", "D", "F"):
    if k in scores:
        s = scores[k]; print(k, s["status_match"], "/", s["n"], "틀린일치", s["false_match"], "재현율", s["ask_recall"], s["wrong"])
print("불안정", unstable, "근거 미확인", unverified)
