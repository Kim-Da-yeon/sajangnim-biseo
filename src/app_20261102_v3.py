"""시연 서버.

흐름: 확정된 공고 조건 로드 → 프로필로 공고별 판정(LLM 없음) → 빠진 항목 질문(인터뷰 에이전트) → 안내 카드(안내 작성 에이전트) → 달력 파일 제공.
목적: 판정은 즉시·재현 가능하게 규칙으로 하고, 대화와 설명에만 LLM을 쓰는 구조를 화면으로 보여준다.
결과 해석: 화면의 결과는 공고 문구와의 대조이며 자격 확정이 아니다.
실행: python src/app_20261102_v3.py → http://127.0.0.1:8000
"""
import glob, json, os, re, sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
import uvicorn

sys.path.insert(0, os.path.dirname(__file__))
from agents_20261102_v6 import FIELDS, R, run_card, run_match, run_questions
from judge_20261102_v5 import OK, NO, ASK, ORG, judge

app = FastAPI()
NOTICES = {}
EXTRA_FIELDS = {"revenue_2025": "2025년 매출액(원)", "revenue_before": "비교 전 기간 매출(원)", "revenue_latest": "최근 기간 매출(원)", "revenue_compare_period": "매출 비교 기간(연도/반기/분기/월)",
                "shared_office": "공유오피스·공유주방 운영 여부", "good_landlord": "착한 임대인 해당 여부", "same_site_6m": "같은 장소에서 6개월 이상 영업", "registered_mlm": "다단계판매업 등록 여부", "blind_massage": "시각장애인 운영 안마원 여부", "sub_industry_excluded": "제외 대상 세부 업종 해당 여부", "applicant_type": "신청 유형"}
NUM = {"employees", "revenue_3y_avg", "revenue_2025", "revenue_prev_year", "mfg_revenue", "revenue_before", "revenue_latest", "policy_loan_count_5y"}
DATE = {"founded_date", "closure_date", "restart_date"}
TEXT = {"main_industry_ksic", "support_field", "special_zone", "hq_region", "factory_region", "site_region", "business_status", "revenue_compare_period", "product_origin", "applicant_type"}
Q_CACHE = f"{R}/results/question_cache.json"
COND_TEXT, STORY = {}, {}
PROGRAMS = {"1071565": ["일반경영안정자금", "긴급경영안정자금(일시적 경영애로)"]}  # 범위로 지정한 자금별로 나눠 보여준다


def load():
    # 평가 추출 결과와 코퍼스 추출 결과를 하나의 목록으로 합친다. 같은 공고면 최신 파일을 쓴다.
    meta = {n["id"]: n for n in json.load(open(f"{R}/data/manifest.json"))["notices"]}
    for p in glob.glob(f"{R}/results/eval_v2_posthoc/extract_*.json") + glob.glob(f"{R}/data/prepared/*.json"):
        d = json.load(open(p))
        # 자격 조건을 추출하지 못한 공고는 조건 없이 '일치'로 보일 수 있어 목록에서 뺀다.
        if sum(c["kind"] != "period" for c in d["conditions"]) < 3:
            continue
        nid = os.path.basename(p).replace("extract_", "").replace("dev_", "").replace(".json", "")
        title = d.get("title") or meta.get(nid, {}).get("title") or nid
        NOTICES[nid] = dict(id=nid, title=title, url=d.get("url") or meta.get(nid, {}).get("url"), conditions=d["conditions"], trace=d.get("trace", []), programs=d.get("programs") or PROGRAMS.get(nid, []), rounds=d.get("rounds"))
        for c in d["conditions"]:
            COND_TEXT[f"c:{nid}:{c['id']}"] = cond_text(c)
    # 정정으로 대체된 공고는 목록에서 뺀다.
    for old in ("1071619", "1070197"):
        NOTICES.pop(old, None)


def need_fields(c, res, p, nid):
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
    if c["check"] == "conflict":
        return []
    # 규칙으로 표현 못 한 조건은 조건별 예/아니오 질문으로 바꾼다.
    if f == "other" or c["check"] == "unsupported":
        return [f"c:{nid}:{c['id']}"]
    if "예외" in res["why"]:
        return [f"{f}_exception"]
    return [f] if f not in p else []


def kind_of(f):
    return "number" if f in NUM else "date" if f in DATE else "text" if f in TEXT else "bool"


def cond_text(c):
    # 조건별 질문과 표에 쓸 설명. 값이 문장이면 값을, 아니면 근거 문구를 쓴다.
    v = c.get("value")
    return v if isinstance(v, str) and len(v) > 6 else c["evidence"]["quote"]


def label_of(f):
    if f.startswith("c:"):
        return COND_TEXT.get(f, f)
    if f.endswith("_exception"):
        return f"{FIELDS.get(f[:-10], f)}: 공고의 예외 사유에 해당"
    # 필드 설명에는 추출 담당용 지시가 섞여 있어, 화면에는 첫 문장의 이름 부분만 쓴다.
    s = FIELDS.get(f) or EXTRA_FIELDS.get(f) or f
    return re.sub(r"\(법 인용 포함\)", "", re.split(r"\. |, 범위|\(값은", s)[0]).strip()


def options_of(f, conds):
    # 고를 수 있는 값이 정해진 질문은 입력칸 대신 선택지로 보여준다.
    if f == "revenue_compare_period":
        return ["연도", "반기", "분기", "월"]
    for c in conds:
        if c["field"] == f and c["op"] == "in" and isinstance(c["value"], list):
            return c["value"] + ["해당 없음"]
    return None


def plain_why(c, st):
    # 내부 필드 이름이 사장님 화면에 나오지 않게 한다.
    return "입력 필요" if st["why"] == f"{c['field']} 입력 필요" else st["why"]


def fill(p):
    # 입력 칸 하나로 받은 값을 조건 필드에 나눠 준다. 사업장이 한 곳인 가게를 기준으로 하며, 답변으로 덮어쓸 수 있다.
    p = dict(p)
    if p.get("site_region"):
        p.setdefault("hq_region", p["site_region"])
    if p.get("revenue_2025") is not None:
        p.setdefault("revenue_prev_year", p["revenue_2025"])
    return p


def story_answers(n, prog, p, story):
    key = (n["id"], prog, story)
    if key not in STORY:
        try:
            STORY[key] = run_match(n["conditions"], p, story, prog)
        except Exception:
            STORY[key] = {}
    return STORY[key]


@app.post("/api/judge")
def api_judge(body: dict):
    p, as_of = fill({k: v for k, v in body["profile"].items() if v not in ("", None)}), body.get("as_of") or datetime.now().strftime("%F")
    story = (body.get("story") or "").strip()
    # 가게 설명은 기간이 지나지 않은 공고에 한해 진술 대조 담당에게 보낸다. 같은 설명은 다시 호출하지 않는다.
    if story:
        open_ids = [(n, prog) for n in NOTICES.values() for prog in (n["programs"] or [None]) if judge(n["conditions"], p, as_of, prog)["period_status"] != "마감"]
        with ThreadPoolExecutor(4) as ex:
            list(ex.map(lambda x: story_answers(x[0], x[1], p, story), open_ids))
    out = []
    for n in NOTICES.values():
        for prog in (n["programs"] or [None]):
            mine = {k.split(":")[2]: v for k, v in p.items() if k.startswith(f"c:{n['id']}:")}
            r = judge(n["conditions"], {**p, "answers": {**STORY.get((n["id"], prog, story), {}), **mine}}, as_of, prog)
            by = {c["id"]: c for c in n["conditions"]}
            rows, asks = [], []
            for cid, st in r["conditions"].items():
                c = by[cid]
                rows.append(dict(id=cid, status=st["status"], why=plain_why(c, st), field=c["field"], label=cond_text(c) if c["field"] == "other" or c["check"] == "unsupported" else label_of(c["field"]), page=c["evidence"]["page"], quote=c["evidence"]["quote"], exception=c.get("exception")))
                if st["status"] == ASK:
                    asks += need_fields(c, st, p, n["id"])
            pc = [c for c in n["conditions"] if c["kind"] == "period"]
            out.append(dict(id=n["id"], title=n["title"], program=prog, url=n["url"], status=r["status"], period=r["period_status"], flags=r["flags"], deciding=r["deciding"], conditions=rows,
                            ask=[dict(field=f, label=label_of(f), kind=kind_of(f), options=options_of(f, n["conditions"])) for f in dict.fromkeys(asks)], period_value=pc[0]["value"] if pc else None, rounds=n["rounds"]))
    order = {OK: 0, ASK: 1, NO: 2}
    out.sort(key=lambda x: (x["period"] == "마감", order[x["status"]], x["title"]))
    return dict(results=out, as_of=as_of, story_used=bool(story))


@app.post("/api/questions")
def api_questions(body: dict):
    # 같은 항목은 한 번만 질문을 만들어 비용을 줄인다.
    cache = json.load(open(Q_CACHE)) if os.path.exists(Q_CACHE) else {}
    todo = [f for f in body["fields"] if f not in cache]
    if todo:
        for q in run_questions([dict(field=f, meaning=label_of(f) + (". 조건을 충족하면 '예'가 되도록 물을 것" if f.startswith("c:") else "")) for f in todo]):
            cache[q["field"]] = q["question"]
        json.dump(cache, open(Q_CACHE, "w"), ensure_ascii=False, indent=1)
    return {f: cache.get(f, label_of(f)) for f in body["fields"]}


@app.post("/api/card")
def api_card(body: dict):
    n = NOTICES[body["id"]]
    p = fill(body["profile"])
    mine = {k.split(":")[2]: v for k, v in p.items() if k.startswith(f"c:{body['id']}:")}
    res = judge(n["conditions"], {**p, "answers": {**STORY.get((body["id"], body.get("program"), (body.get("story") or "").strip()), {}), **mine}}, body.get("as_of") or datetime.now().strftime("%F"), body.get("program"))
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
