"""코퍼스 보완·분류 스크립트.

흐름: 제목 선별에서 빠진 공고 추가 → 기업마당 접수기간 조회 → 본문 기준으로 소상공인 언급·추출 가능 여부 집계 → corpus.json 갱신.
목적: 제목만으로 고른 목록의 누락과 잡음을 줄이고, 오늘 기준 시연 가능한 공고를 가려낸다.
결과 해석: tier는 키워드 기반 1차 분류다. 실제 자격 판단은 추출·판정 단계에서 이루어진다.
"""
import html, importlib.util, json, os, re, subprocess, sys

ROOT = os.path.expanduser("~/sosang_agent/data/corpus")
UA = "Mozilla/5.0"
rows = json.load(open(f"{ROOT}/corpus.json"))
have = {r["id"] for r in rows}

# 수집 스크립트의 함수만 재사용하기 위해 본문 실행부를 잘라 불러온다.
src = open(os.path.expanduser("~/sosang_agent/scripts/collect_corpus_20261102_v1.py")).read().split('os.makedirs(ROOT, exist_ok=True)\nrows =')[0]
ns = {}
exec(src, ns)
EXTRA = {"1064384": "2026년 소상공인 고용보험료 지원사업 공고", "1065015": "2026년 초기창업패키지(일반형) 창업기업 모집공고",
         "1065016": "2026년 창업도약패키지(일반형) 창업기업 모집공고"}
for i, t in EXTRA.items():
    if i not in have:
        r = dict(source="mss", id=i, title=t, registered=None, period=[])
        ns["download"](r)
        rows.append(r)


def biz_period(r):
    s = subprocess.run(["curl", "-sL", "-m", "30", "-A", UA, r["url"]], capture_output=True, text=True, errors="ignore").stdout
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", s, flags=re.S)))
    m = re.search(r"신청기간\s*(20\d\d\.\d\d\.\d\d)\s*~\s*(20\d\d\.\d\d\.\d\d)", t)
    if m:
        r["period"] = [m.group(1).replace(".", "-"), m.group(2).replace(".", "-")]
    else:
        m = re.search(r"신청기간\s*([^ ]+ ?[^ ]*)", t)
        r["period_note"] = m.group(1)[:30] if m else None


TODAY = "2026-11-02"
for r in rows:
    if r["source"] == "bizinfo":
        biz_period(r)
    s = open(f"{ROOT}/{r['text']}").read() if r.get("text") else ""
    r["mentions_merchant"] = len(re.findall("소상공인|소공인", s))
    # 표 형태 공고는 띄어쓰기가 사라질 수 있어 공백을 뺀 본문에서 자격 표현을 찾는다.
    c = re.sub(r"\s+", "", s)
    r["has_eligibility"] = bool(re.search("신청자격|지원대상|신청대상|참여대상|모집대상|지원자격|자격요건|융자대상", c))
    p = r["period"]
    r["open_today"] = None if len(p) < 2 or p[0] == p[1] else p[0] <= TODAY <= p[1]
    title_m = bool(re.search("소상공인|소공인|자영업", r["title"]))
    if not r.get("text") or r.get("chars", 0) < 300:
        r["tier"] = "본문 없음"
    elif not r["has_eligibility"]:
        r["tier"] = "자격 조항 미탐지"
    elif title_m or re.search("재도전|예비창업|초기창업|창업도약|재창업", r["title"]):
        r["tier"] = "핵심"
    elif r["mentions_merchant"] >= 1:
        r["tier"] = "간접(중소기업 사업, 소상공인 언급)"
    else:
        r["tier"] = "제외 후보(소상공인 언급 없음)"
json.dump(rows, open(f"{ROOT}/corpus.json", "w"), ensure_ascii=False, indent=1)
from collections import Counter
print("총", len(rows), Counter(r["tier"] for r in rows))
print("오늘 기간 내", [(r["id"], r["title"][:36], r["period"]) for r in rows if r["open_today"]])
for r in rows:
    if r["tier"] not in ("핵심",):
        print(r["tier"], "|", r["id"], r["title"][:48], r.get("chars"), r["mentions_merchant"], r.get("error", ""))
