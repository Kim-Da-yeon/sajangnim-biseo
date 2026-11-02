"""4차 새 공고 라벨 감수 반영 스크립트.

흐름: v1 라벨을 읽음 → 코덱스 감수 채택 항목 적용 → 저장.
목적: 측정 전 수정 내역을 남긴다. 시스템 결과를 보지 않은 상태에서 수정했다.
결과 해석: AI 초안에 AI 감수를 더한 것이며 사람이 사례별로 검증하지 않았다.
"""
import json, os

L = os.path.expanduser("~/sosang_agent/data/labels")
d = json.load(open(f"{L}/holdout4_1066477.json"))
# 별첨5는 보조비율 표이므로 수도권 허용 대안 조건을 뺀다.
d["conditions"] = [c for c in d["conditions"] if c["id"] != "A3b"]
json.dump(d, open(f"{L}/holdout4_1066477.json", "w"), ensure_ascii=False, indent=1)
d = json.load(open(f"{L}/holdout4_1066053.json"))
for c in d["conditions"]:
    if c["id"] == "C2":
        c["check"] = "profile"
json.dump(d, open(f"{L}/holdout4_1066053.json", "w"), ensure_ascii=False, indent=1)
s = json.load(open(f"{L}/holdout4_cases.json"))
for c in s["cases"]:
    if c["id"] == "IV2":
        c.update(expected="불일치", reason="가평군은 수도권이고 이전 계획이 없어 비수도권 요건 위반. 별첨5는 보조비율 표임")
    if c["id"] == "TP5":
        c.update(expected="불일치", reason="별첨 신청 제외대상 확인 표에 1인기업 여부가 있고 1인기업에 해당")
s["note"] = (s.get("note") or "") + " 코덱스 감수 후 IV2, TP5 수정."
json.dump(s, open(f"{L}/holdout4_cases.json", "w"), ensure_ascii=False, indent=1)
print("반영 완료")
