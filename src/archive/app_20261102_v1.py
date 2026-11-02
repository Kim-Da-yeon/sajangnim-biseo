"""시연 서버.

흐름: 확정된 공고 조건 로드 → 프로필로 공고별 판정(LLM 없음) → 빠진 항목 질문(인터뷰 에이전트) → 안내 카드(안내 작성 에이전트) → 달력 파일 제공.
목적: 판정은 즉시·재현 가능하게 규칙으로 하고, 대화와 설명에만 LLM을 쓰는 구조를 화면으로 보여준다.
결과 해석: 화면의 결과는 공고 문구와의 대조이며 자격 확정이 아니다.
실행: python src/app_20261102_v1.py → http://127.0.0.1:8000
"""
import glob, json, os, sys
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
import uvicorn

sys.path.insert(0, os.path.dirname(__file__))
from agents_20261102_v4 import FIELDS, R, run_card, run_questions
from judge_20261102_v3 import OK, NO, ASK, ORG, judge

app = FastAPI()
NOTICES = {}
EXTRA_FIELDS = {"revenue_2025": "2025년 매출액(원)", "revenue_before": "비교 전 기간 매출(원)", "revenue_latest": "최근 기간 매출(원)", "revenue_compare_period": "매출 비교 기간(연도/반기/분기/월)",
                "shared_office": "공유오피스·공유주방 운영 여부", "good_landlord": "착한 임대인 해당 여부", "same_site_6m": "같은 장소에서 6개월 이상 영업", "registered_mlm": "다단계판매업 등록 여부", "blind_massage": "시각장애인 운영 안마원 여부", "sub_industry_excluded": "제외 대상 세부 업종 해당 여부", "applicant_type": "신청 유형"}
NUM = {"employees", "revenue_3y_avg", "revenue_2025", "revenue_prev_year", "mfg_revenue", "revenue_before", "revenue_latest", "policy_loan_count_5y"}
DATE = {"founded_date", "closure_date", "restart_date"}
TEXT = {"main_industry_ksic", "support_field", "special_zone", "hq_region", "factory_region", "site_region", "business_status", "revenue_compare_period", "product_origin", "applicant_type"}
Q_CACHE = f"{R}/results/question_cache.json"


def load():
    # 평가 추출 결과와 코퍼스 추출 결과를 하나의 목록으로 합친다. 같은 공고면 최신 파일을 쓴다.
    meta = {n["id"]: n for n in json.load(open(f"{R}/data/manifest.json"))["notices"]}
    for p in glob.glob(f"{R}/results/eval_v1/extract_*.json") + glob.glob(f"{R}/results/dev_*.json") + glob.glob(f"{R}/data/prepared/*.json"):
        d = json.load(open(p))
        nid = os.path.basename(p).replace("extract_", "").replace("dev_", "").replace(".json", "")
        title = d.get("title") or meta.get(nid, {}).get("title") or nid
        NOTICES[nid] = dict(id=nid, title=title, url=d.get("url") or meta.get(nid, {}).get("url"), conditions=d["conditions"], trace=d.get("trace", []), programs=d.get("programs") or [], rounds=d.get("rounds"))
    # 정정으로 대체된 공고는 목록에서 뺀다.
    for old in ("1071619", "1070197"):
        NOTICES.pop(old, None)


def need_fields(c, res, p):
    # 판정기가 확인 필요로 낸 조건을 물어볼 항목으로 바꾼다. 파생 개념은 그 입력값을 묻는다.
    f = c["field"]
    if f in ("small_merchant", "small_craft_business"):
        return [x for x in ("main_industry_ksic", "employees", "revenue_3y_avg") if x not in p]
    if f == "annualized_revenue":
        return [x for x in ("founded_date", "revenue_2025") if x not in p]
    if f == "revenue_change_rate":
        return [x for x in ("revenue_compare_period", "revenue_before", "revenue_latest") if x not in p]
    if f == "excluded_industry":
        why = res["why"]
        if "입력 필요" in why:
            return ["main_industry_ksic"]
        out = []
        for k, label in (("착한 임대인", "good_landlord"), ("공유오피스", "shared_office"), ("6개월", "same_site_6m"), ("다단계", "registered_mlm"), ("안마", "blind_massage")):
            if k in why and label not in p:
                out.append(label)
        return out or (["sub_industry_excluded"] if "일부만" in why else [])
    if f == "other" or c["check"] == "conflict":
        return []
    if "예외" in res["why"]:
        return [f"{f}_exception"]
    return [f] if f not in p else []


def kind_of(f):
    return "number" if f in NUM else "date" if f in DATE else "text" if f in TEXT else "bool"


def label_of(f):
    if f.endswith("_exception"):
        return f"{FIELDS.get(f[:-10], f)}: 공고의 예외 사유에 해당"
    return FIELDS.get(f) or EXTRA_FIELDS.get(f) or f


@app.post("/api/judge")
def api_judge(body: dict):
    p, as_of = {k: v for k, v in body["profile"].items() if v not in ("", None)}, body.get("as_of") or datetime.now().strftime("%F")
    out = []
    for n in NOTICES.values():
        for prog in (n["programs"] or [None]):
            r = judge(n["conditions"], p, as_of, prog)
            by = {c["id"]: c for c in n["conditions"]}
            rows, asks = [], []
            for cid, st in r["conditions"].items():
                c = by[cid]
                rows.append(dict(id=cid, status=st["status"], why=st["why"], field=c["field"], label=label_of(c["field"]), page=c["evidence"]["page"], quote=c["evidence"]["quote"], exception=c.get("exception")))
                if st["status"] == ASK:
                    asks += need_fields(c, st, p)
            pc = [c for c in n["conditions"] if c["kind"] == "period"]
            out.append(dict(id=n["id"], title=n["title"], program=prog, url=n["url"], status=r["status"], period=r["period_status"], flags=r["flags"], deciding=r["deciding"], conditions=rows,
                            ask=[dict(field=f, label=label_of(f), kind=kind_of(f)) for f in dict.fromkeys(asks)], period_value=pc[0]["value"] if pc else None, rounds=n["rounds"]))
    order = {OK: 0, ASK: 1, NO: 2}
    out.sort(key=lambda x: (x["period"] == "마감", order[x["status"]], x["title"]))
    return dict(results=out, as_of=as_of)


@app.post("/api/questions")
def api_questions(body: dict):
    # 같은 항목은 한 번만 질문을 만들어 비용을 줄인다.
    cache = json.load(open(Q_CACHE)) if os.path.exists(Q_CACHE) else {}
    todo = [f for f in body["fields"] if f not in cache]
    if todo:
        for q in run_questions([dict(field=f, meaning=label_of(f)) for f in todo]):
            cache[q["field"]] = q["question"]
        json.dump(cache, open(Q_CACHE, "w"), ensure_ascii=False, indent=1)
    return {f: cache.get(f, label_of(f)) for f in body["fields"]}


@app.post("/api/card")
def api_card(body: dict):
    n = NOTICES[body["id"]]
    res = judge(n["conditions"], body["profile"], body.get("as_of") or datetime.now().strftime("%F"), body.get("program"))
    card, banned = run_card(n["title"], res, n["conditions"])
    return dict(card=card, banned=banned)


@app.get("/api/trace/{nid}")
def api_trace(nid: str):
    return NOTICES[nid]["trace"]


@app.get("/api/ics/{nid}")
def api_ics(nid: str):
    # 공고에 표기된 마감일을 달력 파일로 내려준다. 종료일이 없으면 404.
    n = NOTICES[nid]
    pc = [c for c in n["conditions"] if c["kind"] == "period" and isinstance(c["value"], list) and c["value"][1]]
    if not pc:
        return Response(status_code=404)
    d = pc[0]["value"][1][:10].replace("-", "")
    ics = f"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//sosang//KO\r\nBEGIN:VEVENT\r\nUID:{nid}@sosang\r\nDTSTAMP:{d}T000000Z\r\nDTSTART;VALUE=DATE:{d}\r\nSUMMARY:{n['title'][:60]} 신청 마감\r\nDESCRIPTION:공고 확인 필요. {n['url'] or ''}\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
    return Response(ics, media_type="text/calendar", headers={"Content-Disposition": "attachment; filename=deadline.ics"})


@app.get("/")
def home():
    return FileResponse(f"{R}/web/index.html")


if __name__ == "__main__":
    load()
    uvicorn.run(app, host="127.0.0.1", port=8000)
