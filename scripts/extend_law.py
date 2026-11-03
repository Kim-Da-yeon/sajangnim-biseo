"""법령 검색 자료 확장 스크립트.

흐름: law.go.kr에서 받은 법령 원문을 조문 단위로 잘라 law_items.json의 search에 더함 → 최저임금 고시 금액을 항목으로 추가.
목적: 임대차만 묻던 법령 질문을 최저임금, 근로기준, 소상공인 법으로 넓힌다.
결과 해석: 2026-11-03 수집본 기준이다. 일반 정보 안내용이며 개별 사건 판단에 쓰지 않는다. 고시 금액은 언론 보도로 확인한 값이다.
"""
import json, os, re

R = os.path.expanduser("~/sosang_agent")
P = f"{R}/data/law/law_items.json"
d = json.load(open(P))
keep = [a for a in d["search"] if a["id"].startswith(("상가임대차법", "시행령"))]
keep = [dict(a, id=("상가임대차법 시행령" + a["id"][3:]) if a["id"].startswith("시행령") else a["id"]) for a in keep]
LAWS = [("최저임금법", "최저임금법"), ("최저임금법 시행령", "최저임금법시행령"), ("근로기준법", "근로기준법"), ("근로기준법 시행령", "근로기준법시행령"), ("소상공인기본법", "소상공인기본법"), ("소상공인법", "소상공인보호및지원에관한법률"),
        ("퇴직급여법", "근로자퇴직급여보장법"), ("기간제·단시간법", "기간제및단시간근로자보호등에관한법률"), ("남녀고용평등법", "남녀고용평등과일가정양립지원에관한법률"), ("산재보험법", "산업재해보상보험법"), ("식품위생법", "식품위생법"), ("가맹사업법", "가맹사업거래의공정화에관한법률"), ("개인정보보호법", "개인정보보호법"), ("여신전문금융업법", "여신전문금융업법"), ("옥외광고물법", "옥외광고물등의관리와옥외광고산업진흥에관한법률"), ("전자상거래법", "전자상거래등에서의소비자보호에관한법률"), ("부가가치세법", "부가가치세법"), ("중소기업기본법", "중소기업기본법"), ("표시광고법", "표시광고의공정화에관한법률")]
LAWS = [x for x in LAWS if os.path.exists(f"{R}/data/law/{x[1]}.txt")]
add = []
for name, f in LAWS:
    t = re.sub(r"\s+", " ", open(f"{R}/data/law/{f}.txt").read()).replace("( ", "(").replace(" )", ")")
    # 부칙 앞까지만 현행 본문으로 쓴다.
    m = re.search(r"부\s*칙\s*<", t)
    t = t[:m.start()] if m else t
    ms = list(re.finditer(r"제\d+조(?:의\d+)?\([^)]{2,40}\)", t))
    seen = set()
    for a, b in zip(ms, ms[1:] + [None]):
        key = a.group()
        # 본문 앞의 목차와 다른 조문 인용을 건너뛰고 내용이 있는 첫 항목만 쓴다.
        body = t[a.start():b.start() if b else a.start() + 1800].strip()
        if key in seen or len(body) < 25 or "삭제" in body[:len(key) + 8]:
            continue
        seen.add(key)
        add.append(dict(id=f"{name} {key}", text=re.sub(r"\s*(<|&lt;)(개정|신설|시행일)[^>&]*(>|&gt;)", "", body).replace("&lt;", "<").replace("&gt;", ">")[:1800]))
wage = dict(id="최저임금 고시(2026년, 2027년 적용 금액)", text="2026년 최저임금은 시간급 10,320원입니다. 2027년 1월 1일부터 적용되는 최저임금은 시간급 10,700원이고, 주 40시간(월 209시간) 기준 월 환산액은 2,236,300원입니다. 업종 구분 없이 모든 사업장에 동일하게 적용됩니다.")
d["search"] = keep + [wage] + add
d["collected"] = "2026-11-03"
json.dump(d, open(P, "w"), ensure_ascii=False, indent=1)
print(len(keep), len(add), {n: sum(a["id"].startswith(n + " ") for a in add) for n, _ in LAWS})
