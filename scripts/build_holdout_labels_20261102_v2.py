"""새 공고 라벨 감수 반영 스크립트.

흐름: v1이 만든 라벨 JSON을 읽음 → 코덱스 감수 중 원문 대조로 채택한 항목만 적용 → 저장, 채택·불채택 사유를 docs에 기록.
목적: 측정 전 라벨 수정 내역을 코드와 문서로 남긴다. 시스템 결과는 보지 않은 상태에서 수정했다.
결과 해석: AI 초안에 AI 감수를 더한 것이며 참가자 확인 전이다. 불채택 항목은 라벨의 한계로 보고서에 공개한다.
"""
import json, os

L = os.path.expanduser("~/sosang_agent/data/labels")
load = lambda n: json.load(open(f"{L}/holdout_{n}.json"))


def save(n, d):
    json.dump(d, open(f"{L}/holdout_{n}.json", "w"), ensure_ascii=False, indent=1)


def by(d, i):
    return next(c for c in d["conditions"] if c["id"] == i)


# 1066183: 변경 사항은 신청기간 종료일뿐이고 시작일 2.5는 그대로다. 기준서 5장(자격과 무관한 변경은 판정 유지)에 따라 최초 공고일만 쓴다.
d = load("1066183")
d["conditions"] = [c for c in d["conditions"] if c["id"] not in ("G3b", "M4b")]
save("1066183", d)
# 1069948: 법인 설립 완료 요건을 분명히 하고, 협동조합 근거법 요건과 임대업 예외를 적는다.
d = load("1069948")
by(d, "T2")["field"] = "registration_completed"
by(d, "A3")["value"] = "협동조합기본법: 수익사업 영위. 중소기업협동조합법: 정관에 이익 배당 사항 표기 및 수익사업 영위"
by(d, "X6c")["exception"] = "자율상권조합은 조합원이 임대업을 영위해도 신청 가능"
save("1069948", d)
# 1066579: 고정 기준일 1.22는 수정 공고일이 아니다. 전용 값이 없어 as_of_date로 적고 날짜를 note에 남긴다.
d = load("1066579")
for i in ("A1", "A1c", "A3"):
    by(d, i)["basis"] = "as_of_date"
    by(d, i)["note"] = "고정 기준일 2026-01-22"
by(d, "E5")["exception"] = (by(d, "E5").get("exception") or "") + " / 글로벌기업 협업 프로그램, 창업도약패키지 성장촉진 프로그램만 지원받은 자는 신청 가능"
save("1066579", d)
# PBLN127590: 매출 비교 기간을 명시한다.
d = load("PBLN127590")
by(d, "G1")["note"] = "2024년 대비 2025년"
by(d, "B2a")["note"] = by(d, "B2b")["note"] = "2025년 기준"
save("PBLN127590", d)
# BN5: 최초 공고일 2.5 기준 업력 30년 미만이므로 불일치.
s = json.load(open(f"{L}/holdout_cases.json"))
c = next(x for x in s["cases"] if x["id"] == "BN5")
c.update(expected="불일치", reason="모집공고일 2.5 기준 업력 30년 미만. 연장은 신청 종료일만 변경. 기간은 마감", decisive=["G3a"])
c["flags"] = [f for f in c["flags"] if f != "근거 충돌 표시"]
s["note"] = (s.get("note") or "") + " 코덱스 감수 후 BN5 수정."
json.dump(s, open(f"{L}/holdout_cases.json", "w"), ensure_ascii=False, indent=1)
print("반영 완료")
