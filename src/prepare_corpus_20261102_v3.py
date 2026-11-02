"""서비스 공고 조건 확정 스크립트.

흐름: 코퍼스에서 오늘 기준 기간 내 공고와 시연 공고를 골라 총괄 루프로 조건을 확정 → data/prepared에 저장.
목적: 화면에서 '오늘 확인할 수 있는 공고'를 보여준다. 정답 라벨이 없으므로 정확도 평가에는 쓰지 않는다.
결과 해석: 범위를 사업체 신청 자격으로 넓게 지정한 자동 추출 결과이며, 근거 문구 확인 전 단계의 안내 자료다.
"""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
from agents_20261102_v6 import prepare_notice, R

C = json.load(open(f"{R}/data/corpus/corpus.json"))
OUT = f"{R}/data/prepared"
SEL = [r for r in C if r.get("open_today") and r["tier"] == "핵심" and r["id"] != "PBLN_000000000127619"]
SEL += [r for r in C if r["id"] in ("1064384", "1066579", "1068077", "1071870")]  # 고용보험료, 예비창업패키지(수정 2차), 생활문화, 클린제조(연장)


def run(r):
    p = f"{OUT}/{r['source']}_{r['id']}.json"
    if os.path.exists(p):
        return r["id"], "있음"
    text = open(f"{R}/data/corpus/{r['text']}").read()
    out = prepare_notice(r["id"], text, "개별 사업체(또는 개인)가 신청하는 경우의 신청 자격, 제외 조건, 신청기간", [])
    out.update(title=r["title"], url=r["url"], source=r["source"])
    json.dump(out, open(p, "w"), ensure_ascii=False, indent=1)
    return r["id"], len(out["conditions"])


with ThreadPoolExecutor(4) as ex:
    for x in ex.map(run, SEL):
        print(x, flush=True)
