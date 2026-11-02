"""2차 새 공고 라벨 감수 반영 스크립트.

흐름: v1 라벨 JSON을 읽음 → 평창 공고 제외 → 코덱스 감수 채택 항목 적용 → 저장.
목적: 측정 전 수정 내역을 남긴다. 시스템 결과를 보지 않은 상태에서 수정했다.
결과 해석: AI 초안에 AI 감수를 더한 것이며 참가자 확인 전이다.
"""
import json, os

L = os.path.expanduser("~/sosang_agent/data/labels")
s = json.load(open(f"{L}/holdout2_cases.json"))
# 평창 공고 원문은 신청 서식뿐이라 자격 조건이 없다. 측정 전에 제외한다.
s["cases"] = [c for c in s["cases"] if c["notice_id"] != "PBLN127211"]
for c in s["cases"]:
    if c["id"] == "SP5":
        c.update(expected="불일치", reason="신청가능 업력 표는 1.22까지이며 1.23 개업은 범위 밖", flags=[f for f in c["flags"] if f != "근거 충돌 표시"])
    if c["id"] == "IF6":
        c.update(expected="불일치", reason="계획 시설 일부가 공고일 현재 미준공이라 구축 완료 요건 위반")
s["note"] = (s.get("note") or "") + " 평창 제외, 코덱스 감수 후 SP5·IF6 수정."
json.dump(s, open(f"{L}/holdout2_cases.json", "w"), ensure_ascii=False, indent=1)
sc = json.load(open(f"{L}/holdout2_scope.json"))
sc.pop("PBLN127211", None)
json.dump(sc, open(f"{L}/holdout2_scope.json", "w"), ensure_ascii=False, indent=1)
d = json.load(open(f"{L}/holdout2_1065015.json"))
# 업력 표기 충돌로 묶었던 OR 그룹을 풀고 표의 범위를 쓴다.
d["conditions"] = [c for c in d["conditions"] if not (c["id"].startswith("S3") and c["check"] == "conflict")]
for c in d["conditions"]:
    if c["id"].startswith("S3"):
        c["group"] = "AND"
    if c["id"] == "E14":
        c["value"] = "장관이 인정하는 참여 제한 사유에 해당하지 않음"
json.dump(d, open(f"{L}/holdout2_1065015.json", "w"), ensure_ascii=False, indent=1)
print("반영 완료", len(s["cases"]))
