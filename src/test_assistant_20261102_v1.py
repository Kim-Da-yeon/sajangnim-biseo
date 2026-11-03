"""사장님 비서 추가 기능 점검 스크립트.

흐름: 법령 질문 12개의 조문 검색 적중 확인 → 판단 요구 질문의 답변 거절 확인 → 형식이 다른 가상 계약서 5건의 값 추출 비교 → 돈 항목 근거 확인 비율 계산.
목적: 새 기능이 작동하는지 최소한으로 잰다. 정답은 작성자가 조문과 가상 계약서를 보고 정했다.
결과 해석: 소규모 기능 점검이며 법률 정확도 평가가 아니다.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from assistant_20261103_v6 import R, law_answer, lease_read, search_articles

Q = [("임대료 인상 상한이 몇 퍼센트인가요?", "시행령 제4조"), ("재계약 요구는 언제까지 해야 하나요?", "제10조("), ("권리금 보호 기간이 언제부터인가요?", "제10조의4"), ("계약갱신은 최대 몇 년까지 되나요?", "제10조("),
     ("관리비 내역을 달라고 할 수 있나요?", "제19조의2"), ("월세가 몇 번 밀리면 해지될 수 있나요?", "제10조의8"), ("폐업하면 계약을 해지할 수 있나요?", "제11조의2"), ("분쟁이 생기면 어디에 조정을 신청하나요?", "제20조"),
     ("보증금을 돌려받지 못하면 임차권등기는 어떻게 하나요?", "제6조"), ("서울 상가의 보증금 기준 금액은 얼마인가요?", "제2조"), ("확정일자는 어디서 받나요?", "제4조"), ("보증금을 월세로 바꿀 때 비율 제한이 있나요?", "제12조")]
hit = [(q, g, any(g in a["id"] for a in search_articles(q))) for q, g in Q]
R1 = sum(x[2] for x in hit)
judge_q = ["건물주가 나가라고 하는데 제가 이길 수 있나요?", "제 계약서대로면 권리금을 받을 수 있나요?", "소송하면 승소할까요?"]
refuse = [law_answer(q)["out_of_scope"] for q in judge_q]
C = [("임대차 기간: 2025.03.01 ~ 2027.02.28\n보증금 30,000,000원 월세 1,500,000원\n소재지: 서울특별시 마포구 000", ("2025-03-01", "2027-02-28", 30000000, 1500000)),
     ("계약기간은 2024년 7월 1일부터 2026년 6월 30일까지로 한다. 보증금 금 오천만원정, 차임 매월 금 이백만원정. 부산광역시 해운대구 000", ("2024-07-01", "2026-06-30", 50000000, 2000000)),
     ("소재지 대구광역시 중구 000\n기간 2026-01-15 ~ 2028-01-14\n보증금 10,000,000 / 월차임 800,000", ("2026-01-15", "2028-01-14", 10000000, 800000)),
     ("상가 임대차 계약서. 전북특별자치도 정읍시 000. 임대차 기간 2023. 10. 1.부터 2026. 9. 30.까지, 보증금 2천만원, 월세 70만원(부가세 별도)", ("2023-10-01", "2026-09-30", 20000000, 700000)),
     ("경기도 수원시 000. 보증금 100,000,000원, 차임 3,000,000원. 기간은 계약서 별지에 따른다.", (None, None, 100000000, 3000000))]
rows = []
for text, gold in C:
    v = lease_read(text)
    got = (v["start"], v["end"], v["deposit"], v["rent"])
    rows.append(dict(gold=gold, got=got, ok=got == gold, windows=len(v["windows"]), limit=v["limit_label"], quote_errors=v.get("quote_errors")))
money = json.load(open(f"{R}/data/prepared_money.json"))
out = dict(law_retrieval=f"{R1}/{len(Q)}", law_miss=[x[:2] for x in hit if not x[2]], refuse=f"{sum(refuse)}/{len(refuse)}", lease=f"{sum(r['ok'] for r in rows)}/{len(rows)}", lease_rows=rows, money_verified=f"{sum(m.get('verified', False) for m in money.values())}/{len(money)}")
json.dump(out, open(f"{R}/results/assistant_check.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=0)[:1600])
