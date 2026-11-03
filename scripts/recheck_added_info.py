"""최종 판단 지시문 수정 후 사후 점검(4차 24사례 + 입력 보완 사례).

흐름: 4차 오답 사례에 빠져 있던 사실을 설명에 추가 → 저장된 조건·진술 대조·조건 판단으로 최종 판단 2회 실행 → 저장.
목적: 오답 원인이 입력 정보 부족인지 확인한다.
결과 해석: 이미 오답을 본 사례를 고쳐 다시 돌린 사후 점검이다. 주 수치(18/24)를 대체하지 않는다. 기대 상태는 추가한 사실에서 따라오는 값이다.
"""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from agents_round5 import R, run_final

OUT, L = f"{R}/results/holdout4_v1", f"{R}/data/labels"
cases = {c["id"]: c for c in json.load(open(f"{L}/holdout4_cases.json"))["cases"]}
SC = {k: tuple(v) for k, v in json.load(open(f"{L}/holdout4_scope.json")).items()}
# (이름, 사례, 추가 사실, 기대 상태). 카페 겸업은 기술 용도에 따라 결론이 갈리는지 보려고 두 가지로 넣는다.
V = [("가평군_이전계획없음", "IV2", "선정되더라도 사업장을 비수도권으로 옮길 계획은 없습니다.", "불일치"),
     ("카페겸업_카페기술", "TP3", "보호받으려는 핵심기술은 카페에서 쓰는 음료 제조 기술입니다.", "불일치"),
     ("카페겸업_빵기술", "TP3", "보호받으려는 핵심기술은 빵 공장의 제조 공정 기술이고 카페와 무관합니다.", "일치"),
     ("1인기업_기관답변", "TP5", "운영기관에 문의하니 직원 없는 1인기업은 신청 제외 대상이라고 답했습니다.", "불일치"),
     ("백년가게_서류완료", "BN1", "역량기술서를 작성해 두었고 소상공인확인서는 오늘 기준 유효합니다. 개인사업자이고 지정 후 승계는 없습니다.", "일치"),
     ("카페겸업_빵기술_별도사업자", "TP3", "보호받으려는 핵심기술은 빵 공장의 제조 공정 기술이고 카페와 무관합니다. 카페는 별도 사업자이고 이 회사 사업자등록증에는 제조업만 있으며, 창업 제외 업종 표시는 잘못 입력한 값입니다.", "일치"),
     ("백년소공인_다른사유없음", "BN2", "2024년에 처음 규모를 넘었고 그 전 유예 이력이 없습니다. 관계기업 편입 등 다른 사유도 없고 소기업 규모입니다. 유예 상태의 확인서를 발급받을 수 있습니다.", "일치")]


def base(cid):
    ans = {}
    for name in (f"match_A_{cid}_r0.json", f"resolve_{cid}_r0.json"):
        p = f"{OUT}/{name}"
        if os.path.exists(p):
            d = json.load(open(p))
            ans.update(d.get("answers", d) if name.startswith("resolve") else d)
    return {**cases[cid]["profile"], "answers": ans}


def one(job):
    name, cid, extra, want, r = job
    c, prof = cases[cid], base(cid)
    prof["other"] = (prof.get("other") or "") + " " + extra
    n = c["notice_id"]
    ext = json.load(open(f"{OUT}/extract_{n}.json"))
    gold = json.load(open(f"{L}/holdout4_{n}.json"))
    text = open(f"{R}/data/text/{gold['source_text']}.txt").read()
    v = run_final(text, SC[n][0], prof, c["as_of"], ext["conditions"], c["program"])
    return dict(name=name, case=cid, want=want, run=r, status=v["status"], reason=v["reason"], ask=v.get("ask", []), cause=v.get("cause"), org_ask=v.get("org_ask", []), verified=v.get("verified"))


jobs = [(x[0], x[1], x[2], x[3], 0) for x in V] + [("원본_" + cid, cid, "", c["expected"], 0) for cid, c in cases.items()]
with ThreadPoolExecutor(8) as ex:
    res = list(ex.map(one, jobs))
json.dump(res, open(f"{R}/results/recheck_rules.json", "w"), ensure_ascii=False, indent=1)
base_ = [r for r in res if r["name"].startswith("원본_")]
print("원본 24사례 일치", sum(r["status"] == r["want"] for r in base_), "틀린 일치", sum(r["want"] != "일치" and r["status"] == "일치" for r in base_))
for r in res:
    if not r["name"].startswith("원본_") or r["status"] != r["want"]:
        print(r["name"], "기대", r["want"], "→", r["status"], "/", r["cause"], "| 질문", len(r["ask"]), "기관", len(r["org_ask"]), "|", r["reason"][:90])
