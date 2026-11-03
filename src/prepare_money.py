"""공고 돈 항목 추출 스크립트.

흐름: 화면에 나오는 공고의 원문을 읽음 → 자금 해석 에이전트로 지원 방식, 상환 여부, 금액, 자부담 추출 → data/prepared_money.json 저장.
목적: 갚아야 하는 돈인지와 금액을 공고별로 보여준다.
결과 해석: 원문 근거 문구가 확인된 값만 남긴다. 정답 라벨과 비교하지 않은 안내 자료다.
"""
import glob, json, os, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
from assistant_20261102_v5 import money_read, R
import importlib.util
spec = importlib.util.spec_from_file_location("app4", f"{R}/src/app.py")
app4 = importlib.util.module_from_spec(spec); spec.loader.exec_module(app4)
app4.load()
OUT = f"{R}/data/prepared_money.json"
cur = {}  # 매번 새로 추출한다
ids = [n for n in app4.NOTICES if n not in cur and app4.notice_text(n)]


def one(n):
    return n, money_read(app4.notice_text(n))


with ThreadPoolExecutor(5) as ex:
    for n, v in ex.map(one, ids):
        cur[n] = v; print(n, v["kind"], v["repay"], v["amount"][:40], flush=True)
json.dump(cur, open(OUT, "w"), ensure_ascii=False, indent=1)
print(len(cur), "건")
