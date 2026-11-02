"""법령 자료 구축 스크립트.

흐름: law.go.kr에서 받아 둔 조문 텍스트에서 필요한 문구를 그대로 잘라 냄 → data/law/law_items.json과 ontology/law.ttl 저장.
목적: 임대차 기간과 금액 기준, 법령 개정 내용을 원문 그대로 쓰고, 기간 규칙을 온톨로지로 관리한다.
결과 해석: 수집일(2026-11-02) 기준이다. 문구는 원문을 자른 것이며 해석을 더하지 않는다. 요약 한 문장(plain)은 사람이 읽기 쉽게 쓴 것이고 근거는 quote다.
"""
import json, os, re

R = os.path.expanduser("~/sosang_agent")
T = lambda n: re.sub(r"\s+", " ", open(f"{R}/data/law/{n}.txt").read()).replace("( ", "(").replace(" )", ")")
A, D = T("상가건물임대차보호법"), T("상가건물임대차보호법시행령")
U = "https://www.law.go.kr/LSW/lsInfoP.do?lsNm="


def cut(t, start, stop):
    # start부터 stop 앞까지 그대로 잘라 낸다. 못 찾으면 오류로 멈춘다.
    i = t.index(start)
    j = t.index(stop, i + len(start))
    return t[i:j].strip()


clean = lambda s: re.sub(r"\s*<(개정|신설)[^>]*>", "", s).replace(" ,", ",").strip()
arts = {
    "상가임대차법 제10조 제1항": clean(cut(A, "제10조(계약갱신 요구 등) ①", " 1. 임차인이 3기의")),
    "상가임대차법 제10조 제2항": clean(cut(A, "② 임차인의 계약갱신요구권은", " ③ 갱신되는")),
    "상가임대차법 제10조의4 제1항": clean(cut(A, "제10조의4(권리금 회수기회 보호 등) ①", " 1. 임차인이 주선한")),
    "상가임대차법 제11조 제1항": clean(cut(A, "제11조(차임 등의 증감청구권) ①", " ② 제1항에 따른")),
    "상가임대차법 제11조 제2항": clean(cut(A, "② 제1항에 따른 증액 청구는", " ③")),
    "상가임대차법 제2조 제3항": clean(cut(A, "③ 제1항 단서에도 불구하고", " [전문개정 2009. 1. 30.] 제3조")),
    "상가임대차법 제19조의2 제1항": clean(cut(A, "제19조의2(관리비 내역의 제공) ①", " ② 제1항에 따라")),
    "시행령 제4조": clean(cut(D, "제4조(차임 등 증액청구의 기준)", " 제5조")),
    "시행령 제2조": clean(cut(D, "제2조(적용범위) ①", " 제3조(확정일자")),
}
changes = [
    dict(id="상가임대차-관리비", law="상가건물 임대차보호법", date="2026-05-12", when="lease", url=U + "상가건물임대차보호법", plain="임대인에게 관리비를 내면 내역을 요청할 수 있습니다.", quote=arts["상가임대차법 제19조의2 제1항"]),
    dict(id="소상공인법-안전", law="소상공인 보호 및 지원에 관한 법률", date="2026-07-01", when="solo", url=U + "소상공인 보호 및 지원에 관한 법률", plain="1인·여성 소상공인 안전 물품·설비 지원 근거가 생겼습니다.", quote=cut(T("소상공인보호및지원에관한법률.rvs"), "1인 소상공인 및 여성", " <법제처 제공>")),
    dict(id="기본법-종합계획", law="소상공인기본법", date="2026-06-03", when="general", url=U + "소상공인기본법", plain="정부 종합계획에 AI 활용, 에너지 효율화, 지식재산권 지원이 들어갑니다.", quote=cut(T("소상공인기본법.rvs"), "정부가 소상공인의 보호", " <법제처 제공>")),
]
search = []
for n, t, pre in (("상가임대차법", A, "상가임대차법"), ("시행령", D, "시행령")):
    ms = list(re.finditer(r"제\d+조(?:의\d+)?\([^)]{2,30}\)", t))
    for a, b in zip(ms, ms[1:] + [None]):
        body = t[a.start():b.start() if b else a.start() + 1500]
        if "시행일" in a.group() or "다른 법률" in a.group() or "부칙" in body[:20]:
            continue
        search.append(dict(id=f"{pre} {a.group()}", text=clean(body)[:1600]))
search = list({x["id"]: x for x in search}.values())
json.dump(dict(collected="2026-11-02", source=U + "상가건물임대차보호법", articles=arts, changes=changes, search=search), open(f"{R}/data/law/law_items.json", "w"), ensure_ascii=False, indent=1)
ttl = """@prefix sa: <https://sosang.example/ontology#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
# 임대차 기간 규칙과 지역별 보증금액. 값은 data/law의 조문을 옮긴 것이다.
sa:Renewal a sa:LeaseWindow ; rdfs:label "계약갱신 요구 기간" ; sa:monthsBefore 6 ; sa:monthsBeforeEnd 1 ; sa:article "상가임대차법 제10조 제1항" .
sa:Premium a sa:LeaseWindow ; rdfs:label "권리금 회수기회 보호 기간" ; sa:monthsBefore 6 ; sa:monthsBeforeEnd 0 ; sa:article "상가임대차법 제10조의4 제1항" .
sa:Seoul a sa:RegionLimit ; rdfs:label "서울특별시 9억원" ; sa:amount 900000000 ; sa:keywords "서울" .
sa:Busan a sa:RegionLimit ; rdfs:label "부산광역시 6억9천만원" ; sa:amount 690000000 ; sa:keywords "부산" .
sa:Metro a sa:RegionLimit ; rdfs:label "광역시 등 5억4천만원" ; sa:amount 540000000 ; sa:keywords "대구|광주광역시|대전|울산|세종|파주|화성|안산|용인|김포" .
sa:Other a sa:RegionLimit ; rdfs:label "그 밖의 지역 3억7천만원" ; sa:amount 370000000 ; sa:keywords "포항|보은|정읍|제주|강원|전라|충청|경상|전북|전남|충북|충남|경북|경남" .
"""
open(f"{R}/ontology/law.ttl", "w").write(ttl)
print(len(arts), "조문", len(search), "검색", [c["id"] for c in changes])
