"""규칙 판정기.

흐름: 온톨로지 로드 → 파생 개념(소상공인·소공인·제외 업종·연 환산 매출·매출 증감률) 계산 → 조건별 상태 → OR 그룹·공고 상태 합산 → 신청기간 상태 산출.
목적: 최종 판정을 LLM이 아니라 규칙이 내리게 해, 같은 조건·프로필·기준일이면 같은 결과가 나오게 한다.
결과 해석: '일치'는 공고의 확인 가능한 조건과의 대조 결과이며 자격 확정이 아니다. 최종 자격은 주관기관이 판단한다.
"""
import os
import threading
from datetime import date
from functools import lru_cache

import rdflib

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SA = rdflib.Namespace("https://sosang.example/ontology#")
OK, NO, ASK, ORG = "일치", "불일치", "확인 필요", "기관 판단"
ONTO = rdflib.Graph().parse(f"{R}/ontology/sosang.ttl")
QUERY_LOCK = threading.Lock()
SHAPES = rdflib.Graph().parse(f"{R}/ontology/shapes.ttl")
REGION_FIELDS = {"hq_region", "factory_region", "site_region"}
BROAD_TEXT = {"support_field"}
CLOSED_TEXT = {"business_status", "main_industry_ksic"}  # 값 목록이 닫혀 있어 표기가 다르면 곧 다른 값인 필드
SECTION_10 = {"B", "C", "F", "H"}  # 광업·제조업·건설업·운수업은 상시근로자 10명 미만, 그 외 5명 미만(공고 원문)


@lru_cache(maxsize=None)
def section_of(code):
    # 업종 코드 앞 2자리에서 대분류를 그래프 관계(sa:broader)로 찾는다. SPARQL 파서가 스레드에 안전하지 않아 잠금을 쓴다.
    q = f'SELECT ?c WHERE {{ ?n <{SA}code> "{code[:2]}" ; <{SA}broader> ?b . ?b <{SA}code> ?c }}'
    with QUERY_LOCK:
        r = list(ONTO.query(q))
    return str(r[0][0]) if r else None


def size_limits(code):
    # 출처별 소기업 매출 기준을 모두 돌려준다. 3자리(E36 등) → 중분류(C10 등) → 대분류 순으로 찾는다.
    sec, out = section_of(code), {}
    for src in ONTO.subjects(rdflib.RDF.type, SA.Source):
        rules = {str(ONTO.value(r, SA.code)): int(ONTO.value(r, SA.maxRevenue)) for r in ONTO.subjects(SA.source, src)}
        for key in (f"{sec}{code[:2]}", sec):
            if key in rules:
                out[str(ONTO.value(src, rdflib.RDFS.label))] = rules[key]
                break
    return out


def small_merchant(p):
    # 소상공인 = 업종별 소기업 매출 기준 AND 업종별 상시근로자 기준. 확인서가 있으면 수치 입력 없이 인정한다.
    code, emp = p.get("main_industry_ksic"), p.get("employees")
    rev = p.get("revenue_3y_avg", p.get("revenue_2025"))
    if code and emp is not None and emp >= (10 if section_of(code) in SECTION_10 else 5):
        return NO, f"상시근로자 {emp}명은 업종 기준 초과"
    if p.get("merchant_certificate") is True:
        return OK, "소상공인확인서 보유"
    if not code or emp is None or rev is None:
        return ASK, "업종, 상시근로자 수, 매출 입력 필요"
    limits = size_limits(code)
    if not limits:
        return ASK, "업종의 매출 기준을 찾지 못함"
    res = {src: rev <= v for src, v in limits.items()}
    if all(res.values()):
        return OK, "매출·근로자 기준 충족"
    if not any(res.values()):
        return NO, "매출이 소기업 기준 초과"
    return ASK, f"공고별 매출 기준이 달라 판단 불가: {limits}"


def small_craft(p):
    # 소공인 = 소상공인 AND 제조업(C10~C34) AND 상시근로자 10명 미만.
    code = p.get("main_industry_ksic")
    if code and section_of(code) != "C":
        return NO, "제조업 아님"
    return small_merchant(p)


def excluded_industry(p, program=None):
    # 값이 참이면 "제외 업종이 아님"이 아니라 "제외 업종임"을 뜻한다. 직접 입력값이 있으면 그대로 쓴다.
    if "excluded_industry" in p:
        return p["excluded_industry"], "입력값"
    code = p.get("main_industry_ksic")
    if not code:
        return None, "업종 입력 필요"
    hit = None
    for e in ONTO.subjects(SA.list, SA.PolicyFundExclusion):
        c = str(ONTO.value(e, SA.code))
        if code.startswith(c):
            hit = e
            break
    if hit is None:
        return False, "제외 목록에 없음"
    pending = []
    for x in ONTO.subjects(rdflib.RDF.type, SA.ExclusionException):
        if not code.startswith(str(ONTO.value(x, SA.code))):
            continue
        kind, field = str(ONTO.value(x, SA.kind)), ONTO.value(x, SA.field)
        if kind == "allow":
            return False, f"예외 허용: {ONTO.value(x, rdflib.RDFS.label)}"
        if kind.startswith("program:") and kind != f"program:{program}":
            continue
        v = p.get(str(field))
        if v is True:
            return False, f"예외 허용: {ONTO.value(x, rdflib.RDFS.label)}"
        if v is None:
            pending.append(str(ONTO.value(x, rdflib.RDFS.label)))
    if pending:
        return None, "예외 해당 여부 확인 필요: " + ", ".join(pending)
    if str(ONTO.value(hit, SA.partial)) == "true" and p.get("sub_industry_excluded") is None:
        return None, f"코드의 일부만 제외: {ONTO.value(hit, rdflib.RDFS.label)} 해당 여부 확인 필요"
    return True, f"제외 업종: {ONTO.value(hit, rdflib.RDFS.label)}"


def annualized_revenue(p):
    # 2024년 이전 개업은 신고 매출, 2025년 개업은 월평균×12(1개월 미만 끝수는 1개월). 바우처 공고 산식.
    rev, f = p.get("revenue_2025"), p.get("founded_date")
    if rev is None or not f:
        return None
    y, m = int(f[:4]), int(f[5:7])
    if y <= 2024:
        return rev
    if y == 2025:
        return rev / (12 - m + 1) * 12
    return None


def change_rate(p):
    if p.get("revenue_compare_period") and p.get("revenue_before") and p.get("revenue_latest") is not None:
        return (p["revenue_latest"] - p["revenue_before"]) / p["revenue_before"]
    return None


def compare(op, val, target):
    if op == "eq": return val == target
    if op == "ne": return val != target
    if op == "lt": return val < target
    if op == "le": return val <= target
    if op == "gt": return val > target
    if op == "ge": return val >= target
    if op == "in": return val in target
    if op == "not_in": return val not in target
    if op == "between":
        a, b = target
        if isinstance(val, str) and len(a) >= 2 and a[0].isalpha():
            return a <= "C" + val[:2] <= b
        return a <= val <= b
    raise ValueError(op)


def same_text(a, b):
    # 표기 차이만 흡수한다. '공정기술형'과 '공정기술'은 같고, '패션'과 '공정기술'은 다르다.
    a, b = str(a).replace(" ", ""), str(b).replace(" ", "")
    return a == b or a in b or b in a


def region_state(val, target):
    # 시군구가 같으면 일치, 다르면 불일치. '충청북도'처럼 광역 단위만 적힌 조건에 시군구만 입력되면 소속을 물어야 한다.
    vs, ts = str(val).split(), str(target).split()
    if not vs or not ts:
        return None
    if vs[-1] == ts[-1] or same_text(val, target):
        return True
    if ts[-1].endswith(("도", "특별시", "광역시")) and len(vs) == 1:
        return None
    return False


def text_state(field, op, val, target):
    # 문자열 조건 대조. 참·거짓·None(표기만으로 판단 불가)을 돌려준다. 해당 없는 경우 NotImplemented.
    if op not in ("eq", "ne", "in", "not_in") or not isinstance(val, str):
        return NotImplemented
    items = target if isinstance(target, list) else [target]
    if not all(isinstance(x, str) for x in items) or field in CLOSED_TEXT:
        return NotImplemented
    if field in REGION_FIELDS:
        st = [region_state(val, x) for x in items]
        hit = True if True in st else None if None in st else False
    else:
        # 지원 분야는 상위 분류('생활문화형')와 하위 분류('패션')가 섞여 적히므로 다르게 보여도 불일치로 단정하지 않는다.
        hit = any(same_text(val, x) for x in items)
        if not hit and field in BROAD_TEXT:
            hit = None
    if hit is None:
        return None
    return hit if op in ("eq", "in") else not hit


def field_value(field, p, program):
    # 조건 필드를 프로필 값으로 푼다. 파생 필드는 온톨로지 규칙으로 계산한다.
    if field == "excluded_industry":
        return excluded_industry(p, program)
    if field == "annualized_revenue":
        return annualized_revenue(p), "연 환산 매출"
    if field == "revenue_change_rate":
        return change_rate(p), "비교 기간 매출로 계산"
    # 앞선 모집에 신청하지 않았다면 선정됐을 수도 없다.
    if field == "selected_earlier_round" and p.get(field) is None and p.get("applied_earlier_round") is False:
        return False, "앞선 모집 미신청"
    return p.get(field), "입력값"


def check_condition(c, p, program, ontology=True):
    """조건 하나의 상태와 사유를 돌려준다. ontology=False는 온톨로지 제거 비교군이다."""
    if c["check"] in ("discretionary",):
        return ORG, "기관이 판단하는 항목"
    # 사장님의 답변이나 진술 대조 결과가 있으면 그 값으로 대조한다. 공고 안의 표기 충돌은 답변으로 풀 수 없다.
    ans = (p.get("answers") or {}).get(c["id"])
    if ans is not None and c["check"] != "conflict":
        return (OK, "사장님 답변 기준") if ans else (NO, "사장님 답변 기준")
    if c["check"] == "unsupported":
        return ASK, "규칙으로 표현하지 못한 조건이라 답변 필요"
    field, op, target = c["field"], c["op"], c["value"]
    if not ontology and field in ("small_merchant", "small_craft_business"):
        return (OK, "확인서 입력") if p.get("merchant_certificate") else (ASK, "개념 정의가 없어 판단 불가")
    if not ontology and field == "excluded_industry" and "excluded_industry" not in p:
        return ASK, "제외 업종 목록이 없어 판단 불가"
    if field == "small_merchant":
        return small_merchant(p)
    if field == "small_craft_business":
        return small_craft(p)
    v, why = field_value(field, p, program)
    if field == "excluded_industry" and v is None:
        return ASK, why
    if v is None:
        return ASK, f"{field} 입력 필요"
    try:
        ts = text_state(field, op, v, target)
        if ts is None:
            return ASK, "입력값과 공고 표기가 달라 확인 필요"
        if field == "main_industry_ksic" and op == "eq":
            hit = "C" + v[:2] == target
        elif ts is not NotImplemented:
            hit = ts
        else:
            hit = compare(op, v, target)
    except (TypeError, ValueError):
        return ASK, "조건 값 형식을 해석하지 못함"
    if c["check"] == "conflict":
        return (ASK, "공고 안의 표기가 서로 달라 판단 불가") if hit else (NO, "조건과 다름")
    if hit:
        return OK, why
    if c.get("exception") and field != "excluded_industry":
        # 제외 업종 예외는 온톨로지에서 이미 처리했다. 그 밖의 원문 예외는 있으면 해당 여부를 물어야 한다. 입력이 없으면 위반으로 단정하지 않는다.
        ex = p.get(f"{field}_exception")
        if ex is None:
            return ASK, "예외 해당 여부 확인 필요: " + c["exception"]
        return (OK, "예외 해당") if ex else (NO, "조건과 다름, 예외 아님")
    return NO, f"조건과 다름 ({why})"


def applies(c, program, applicant):
    return c.get("applies_to") in (None, program, applicant)


def period_status(conds, as_of):
    ps = [c for c in conds if c["kind"] == "period"]
    if not ps:
        return "일정 확인 필요", []
    c, flags = ps[0], []
    ex = (c.get("exception") or "") + (c.get("note") or "")
    if "조기 마감" in ex:
        flags.append("조기 마감 가능 표시")
    if "표기" in ex:
        flags.append("일정 표기 불일치 표시")
    if c["op"] == "ge" or not isinstance(c["value"], list) or len(c["value"]) != 2 or not c["value"][1]:
        start = c["value"][0] if isinstance(c["value"], list) and c["value"] else c["value"]
        if not start or as_of >= str(start)[:10]:
            return "일정 확인 필요", flags
        return "접수 전", flags
    a, b = c["value"]
    if as_of < a[:10]:
        return "접수 전", flags
    return ("공고상 기간 내" if as_of <= b[:10] else "마감"), flags


def judge(conditions, profile, as_of, program=None, ontology=True):
    """공고 상태, 조건별 상태, 기간 상태, 표시 항목을 돌려준다."""
    applicant = profile.get("applicant_type")
    active = [c for c in conditions if c["kind"] != "period" and applies(c, program, applicant)]
    states = {c["id"]: check_condition(c, profile, program, ontology) for c in active}
    # OR 그룹: 하나라도 일치 → 일치, 전부 불일치 → 불일치, 그 외 확인 필요
    groups = {}
    for c in active:
        if c["group"].startswith("OR:"):
            groups.setdefault(c["group"], []).append(c["id"])
    summary, reason = [], {}
    for g, ids in groups.items():
        st = [states[i][0] for i in ids]
        s = OK if OK in st else NO if all(x == NO for x in st) else ASK
        summary.append(s)
        reason[g] = dict(status=s, members=ids)
    for c in active:
        s = states[c["id"]][0]
        if not c["group"].startswith("OR:") and s != ORG:
            summary.append(s)
    overall = NO if NO in summary else ASK if ASK in summary else OK
    deciding = []
    if overall != OK:
        target = overall
        for c in active:
            g, s = c["group"], states[c["id"]][0]
            if g.startswith("OR:"):
                # 대안 중 기관 판단 항목이 있어 그룹이 확인 필요가 되면 그 항목도 사유로 보여준다.
                if reason[g]["status"] == target and c["id"] not in deciding and (s == target or s == ORG):
                    deciding.append(c["id"])
            elif s == target:
                deciding.append(c["id"])
    per, flags = period_status(conditions, as_of)
    # 기관 판단 항목은 합산에서 빼되, 전체 상태와 관계없이 항상 표시한다.
    if any(states[c["id"]][0] == ORG for c in active):
        flags.append("기관 판단 표시")
    if any(c["check"] == "conflict" and states[c["id"]][0] == ASK for c in active):
        flags.append("근거 충돌 표시")
    return dict(status=overall, period_status=per, deciding=deciding, flags=flags,
                conditions={k: dict(status=v[0], why=v[1]) for k, v in states.items()})


def to_graph(conditions, notice_id="x"):
    # 조건을 RDF로 옮겨 SHACL 검증에 쓴다.
    g = rdflib.Graph()
    for c in conditions:
        n, e = SA[f"cond_{notice_id}_{c['id']}"], SA[f"ev_{notice_id}_{c['id']}"]
        g.add((n, rdflib.RDF.type, SA.Condition))
        for k, pred in (("field", SA.field), ("op", SA.op), ("kind", SA.kind), ("check", SA.check)):
            if c.get(k) is not None:
                g.add((n, pred, rdflib.Literal(str(c[k]))))
        ev = c.get("evidence") or {}
        if ev:
            g.add((n, SA.supportedBy, e))
            g.add((e, rdflib.RDF.type, SA.Evidence))
            if ev.get("quote"):
                g.add((e, SA.quote, rdflib.Literal(ev["quote"])))
            if ev.get("page") is not None:
                g.add((e, SA.page, rdflib.Literal(int(ev["page"]), datatype=rdflib.XSD.integer)))
    return g


def validate_graph(conditions, notice_id="x"):
    # SHACL 위반을 조건 id와 메시지로 돌려준다. 위반이 있으면 재추출 대상이다.
    import pyshacl  # 배포 환경의 판정에는 쓰지 않아 필요할 때만 불러온다
    ok, report, _ = pyshacl.validate(to_graph(conditions, notice_id), shacl_graph=SHAPES, inference="none")
    errs = []
    for r in report.subjects(rdflib.RDF.type, rdflib.URIRef("http://www.w3.org/ns/shacl#ValidationResult")):
        errs.append(dict(node=str(report.value(r, rdflib.URIRef("http://www.w3.org/ns/shacl#focusNode"))).split("#")[-1],
                         message=str(report.value(r, rdflib.URIRef("http://www.w3.org/ns/shacl#resultMessage")))))
    return ok, errs
