"""참가자 확인 라벨 반영과 재채점 스크립트.

흐름: 참가자 답(항목 3, 4, 5, 8)으로 정답 수정 → 저장된 시스템 응답을 새 정답으로 재채점 → results/rescore_participant.json 저장.
목적: API를 다시 호출하지 않고 정답 변경의 효과만 계산한다.
결과 해석: 전체 점수를 본 뒤 수정한 정답이다. 시스템은 다시 실행하지 않았고 코드도 고치지 않았다. 2번 항목(기관 판단 처리)은 미반영.
"""
import json, os

R = os.path.expanduser("~/sosang_agent")
L = f"{R}/data/labels"
load = lambda f: json.load(open(f"{L}/{f}.json"))
save = lambda f, d: json.dump(d, open(f"{L}/{f}.json", "w"), ensure_ascii=False, indent=1)


def cond(d, i):
    return next(c for c in d["conditions"] if c["id"] == i)


# 3번: 보은군 사업장만 있어도 일치
d = load("eval_PBLN127619"); cond(d, "C1c")["check"] = "profile"; cond(d, "C1c")["exception"] = None; save("eval_PBLN127619", d)
s = load("eval_cases")
for c in s["cases"]:
    if c["id"] == "BE4":
        c.update(expected="일치", reason="참가자 확인: 사업장만 보은군이어도 소재지 요건 충족", decisive=[], flags=[f for f in c["flags"] if f != "근거 충돌 표시"])
save("eval_cases", s)
# 4번: 백년소상공인 업력은 연장 공고일 3.11 전일까지
d = load("holdout_1066183"); cond(d, "G3a")["value"] = "1996-03-10"; cond(d, "M4a")["value"] = "2011-03-10"; save("holdout_1066183", d)
# 5번: 국세청 자료 미확인자 제외는 필수 조건. 사장님이 알 수 없으므로 값이 없으면 확인 필요
d = load("holdout_PBLN127594"); cond(d, "C8")["check"] = "unsupported"; save("holdout_PBLN127594", d)
s = load("holdout_cases")
for c in s["cases"]:
    if c["id"] == "BN5":
        c.update(expected="일치", reason="참가자 확인: 연장 공고일 3.11 기준 업력 30년 이상. 기간은 마감", decisive=[])
    if c["id"] in ("JE1", "JE2"):
        c.update(expected="확인 필요", reason="참가자 확인: 국세청 매출자료 확인은 필수 조건이나 값 없음", decisive=["C8"])
save("holdout_cases", s)
# 8번: 술을 파는 음식점도 주류 판매업체로 불일치
s = load("holdout2_cases")
for c in s["cases"]:
    if c["id"] == "TX5":
        c.update(expected="불일치", reason="참가자 확인: 술을 파는 음식점도 주류 판매업체")
save("holdout2_cases", s)

OUT = {}
for name, res, cases in (("eval_v1", "eval_v1", "eval_cases"), ("eval_post", "eval_v2_posthoc", "eval_cases"), ("h1", "holdout_v1", "holdout_cases"), ("h1_fix", "holdout_v1_fix", "holdout_cases"), ("h2", "holdout2_v1", "holdout2_cases")):
    r = json.load(open(f"{R}/results/{res}/results.json"))["cases"]
    cs = load(cases)["cases"]
    OUT[name] = {}
    for a in next(iter(r.values())):
        ok = [c for c in cs if r[c["id"]][a]["status"] == c["expected"]]
        ask = [c for c in cs if c["expected"] == "확인 필요"]
        OUT[name][a] = dict(status_match=len(ok), n=len(cs), false_match=sum(c["expected"] != "일치" and r[c["id"]][a]["status"] == "일치" for c in cs),
                            ask_recall=f"{sum(r[c['id']][a]['status'] == '확인 필요' for c in ask)}/{len(ask)}", wrong=[f"{c['id']}:{c['expected']}→{r[c['id']][a]['status']}" for c in cs if c not in ok])
json.dump(OUT, open(f"{R}/results/rescore_participant.json", "w"), ensure_ascii=False, indent=1)
for k, v in OUT.items():
    print(k, {a: (x["status_match"], x["false_match"], x["ask_recall"]) for a, x in v.items()})
print("h2 A wrong", OUT["h2"]["A"]["wrong"], "D wrong", OUT["h2"]["D"]["wrong"])
