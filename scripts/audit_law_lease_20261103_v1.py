"""법령·임대차 정확성 점검.

흐름: 가상 계약서 5건의 법정 기간과 보증금 구간을 조문 기준 손 계산값과 비교(LLM 호출은 계약서 읽기만) → 법령 질문 12개의 답변과 근거 조문을 저장 → 독립 검수 입력을 만든다.
목적: 기존 점검이 추출·검색 적중만 본 빈틈을 메운다. 계산과 답변 내용 자체를 본다.
결과 해석: 작성자가 정한 소규모 점검이며 전문가 검증이 아니다. 조문은 2026-11-02 수집본 기준이다.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from assistant_20261103_v6 import R, law_answer, lease_read

# 조문: 갱신 요구 만료 6개월 전~1개월 전(제10조 제1항), 권리금 만료 6개월 전~종료(제10조의4 제1항), 보증금 구간(시행령 제2조 제1항)
C = [("임대차 기간: 2025.03.01 ~ 2027.02.28\n보증금 30,000,000원 월세 1,500,000원\n소재지: 서울특별시 마포구 000", "2026-08-28", "2027-01-28", "2027-02-28", 900000000),
     ("소재지 대구광역시 중구 000\n기간 2026-01-15 ~ 2028-01-14\n보증금 10,000,000 / 월차임 800,000", "2027-07-14", "2027-12-14", "2028-01-14", 540000000),
     ("상가 임대차 계약서. 전북특별자치도 정읍시 000. 임대차 기간 2023. 10. 1.부터 2026. 9. 30.까지, 보증금 2천만원, 차임 월 70만원", "2026-03-30", "2026-08-30", "2026-09-30", 370000000),
     ("소재지 부산광역시 해운대구 000. 2024년 8월 31일부터 2026년 8월 31일까지. 보증금 오천만원, 차임 월 이백만원", "2026-02-28", "2026-07-31", "2026-08-31", 690000000),
     ("소재지 경기도 파주시 000. 기간 2025-12-31 ~ 2027-12-31. 보증금 3천만원, 차임 월 100만원", "2027-06-30", "2027-11-30", "2027-12-31", 540000000)]
lease = []
for text, a, b, c, lim in C:
    v = lease_read(text)
    w = {x["id"]: x for x in v["windows"]}
    lease.append(dict(text=text[:40], renewal=(w.get("Renewal", {}).get("start"), w.get("Renewal", {}).get("end")), premium=(w.get("Premium", {}).get("start"), w.get("Premium", {}).get("end")), limit=v.get("limit"), limit_label=v.get("limit_label"),
                      ok_renewal=(w.get("Renewal", {}).get("start"), w.get("Renewal", {}).get("end")) == (a, b), ok_premium=(w.get("Premium", {}).get("start"), w.get("Premium", {}).get("end")) == (a, c), want_limit=lim))
Q = ["임대료 인상 상한이 몇 퍼센트인가요?", "재계약 요구는 언제까지 해야 하나요?", "관리비 내역을 달라고 할 수 있나요?", "월세가 몇 번 밀리면 해지될 수 있나요?", "권리금 회수 기간은 언제까지인가요?", "계약갱신은 최대 몇 년까지 가능한가요?",
     "보증금을 돌려받지 못하면 임차권등기는 어떻게 하나요?", "서울 상가의 보증금 기준 금액은 얼마인가요?", "폐업하면 계약을 해지할 수 있나요?", "월세로 전환할 때 산정률 제한이 있나요?", "소액 임차인 우선변제 금액은 얼마인가요?", "최근 임대차법에서 바뀐 내용이 있나요?",
     # 아래 8개는 검색 수정 후 처음 넣은 질문이다.
     "상가 임대차 최소 기간은 몇 년인가요?", "건물주가 바뀌면 제 임대차 계약은 어떻게 되나요?", "확정일자는 어디서 받나요?", "표준계약서가 있나요?", "부산 상가 보증금 기준 금액은 얼마인가요?", "권리금이 뭔가요?", "경기도 화성시 상가의 보증금 기준 금액은 얼마인가요?", "월세로 전환할 때 산정률 기준은 몇 퍼센트인가요?"]
law = []
for q in Q:
    a = law_answer(q)
    law.append(dict(q=q, answer=a["answer"], used=a["used"], out_of_scope=a["out_of_scope"], unknown=a["unknown_cites"]))
json.dump(dict(lease=lease, law=law), open(f"{R}/results/audit_law_lease_20261103.json", "w"), ensure_ascii=False, indent=1)
for r in lease:
    print(r["text"][:26], r["renewal"], r["ok_renewal"], r["premium"], r["ok_premium"], r["limit_label"], r["want_limit"])
for r in law:
    print("Q", r["q"], "|", r["answer"][:170], "|", r["used"][:2], r["unknown"])
