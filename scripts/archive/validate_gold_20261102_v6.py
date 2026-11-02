"""정답 라벨 검증 스크립트.

흐름: 라벨 JSON 읽기 → 필드·연산자 어휘 확인 → 근거 문구가 원문에 실제로 있는지 확인 → 쪽 번호 대조.
목적: 라벨 오타와 존재하지 않는 인용이 평가 지표를 오염시키는 일을 막는다.
결과 해석: 오류가 0건이면 형식과 인용만 통과한 것이며, 해석이 맞다는 뜻은 아니다.
"""
import json, os, re, sys

ROOT = os.path.expanduser("~/sosang_agent/data")
FIELDS = {"main_industry_ksic", "employees", "small_merchant", "small_craft_business", "revenue_prev_year", "revenue_3y_avg",
          "revenue_change_rate", "annualized_revenue", "closure_history", "restart_date", "product_origin", "applied_earlier_round", "multiple_business_applying", "misuse_history", "social_issue", "air_crash_victim_cert", "single_application", "joint_rep_main", "registration_or_activity", "can_participate", "hq_region", "factory_region", "site_region", "closure_date", "rental_only_individual", "can_restart_by_deadline", "closure_before_restart", "conversion_only", "registration_completed", "all_reps_eligible", "bank_account_available", "program_staff", "subsidy_excluded", "merchant_certificate", "registration_includes_mfg", "domestic_site", "tops_selected_2026", "prior_smart_benefit", "credit_info_listed", "region_site", "preparing_food_startup_in_region", "can_start_within_3m", "social_insurance_arrears", "business_registration", "head_office", "recoup_outstanding", "startup_excluded_industry", "prior_restart_program", "current_startup_program", "mfg_revenue", "business_status", "founded_date", "tax_arrears", "debt_default",
          "gov_sanction", "prior_similar_benefit", "own_brand", "support_field", "special_zone", "policy_loan_count_5y",
          "unfair_trade_1y", "wage_arrears_listed", "nonprofit", "excluded_industry", "application_period", "other"}
OPS = {"eq", "ne", "lt", "le", "gt", "ge", "in", "not_in", "between", "derived"}
KINDS = {"eligibility", "exclusion", "period"}
CHECK = {"profile", "declared", "discretionary", "unsupported"}


def norm(s):
    # PDF 추출 시 공백이 사라지는 경우가 많아 공백을 모두 제거하고 비교한다.
    return re.sub(r"\s+", "", s)


def pages(path):
    # 추출 텍스트의 [[pN]] 표시로 쪽을 나눈다.
    parts = re.split(r"\[\[p(\d+)\]\]", open(path).read())
    return {int(parts[i]): norm(parts[i + 1]) for i in range(1, len(parts), 2)}


errors = 0
for path in sys.argv[1:]:
    g = json.load(open(path))
    pg = pages(f"{ROOT}/text/{g['source_text']}.txt")
    for c in g["conditions"]:
        for key, allowed in (("field", FIELDS), ("op", OPS), ("kind", KINDS), ("check", CHECK)):
            if c[key] not in allowed:
                print("어휘 오류", c["id"], key, c[key]); errors += 1
        for key in ("applies_to", "waives"):
            if key not in c:
                print("필드 누락", c["id"], key); errors += 1
        for w in c.get("waives", []):
            if w not in {x["id"] for x in g["conditions"]}:
                print("면제 대상 없음", c["id"], w); errors += 1
        if not (c["group"] == "AND" or c["group"].startswith("OR:")):
            print("group 오류", c["id"], c["group"]); errors += 1
        q, p = norm(c["evidence"]["quote"]), c["evidence"]["page"]
        found = [k for k, v in pg.items() if q in v]
        if p not in found:
            print("인용 오류", c["id"], "기재쪽", p, "실제", found, c["evidence"]["quote"][:40]); errors += 1
    print(os.path.basename(path), "조건", len(g["conditions"]), "누적 오류", errors)
# 사례 파일: 결정 조건 id와 정답 어휘를 확인한다.
d = os.path.dirname(sys.argv[1]) if sys.argv[1:] else "."
if os.path.exists(f"{d}/eval_cases.json"):
    for x in json.load(open(f"{d}/eval_cases.json"))["cases"]:
        ids = {k["id"] for k in json.load(open(f"{d}/eval_{x['notice_id']}.json"))["conditions"]}
        for k in x["decisive"]:
            if k not in ids:
                print("사례 오류", x["id"], k); errors += 1
        if x["expected"] not in ("일치", "불일치", "확인 필요") or (x["expected"] == "일치") != (not x["decisive"]):
            print("정답 오류", x["id"]); errors += 1
    print("사례 검증 후 누적 오류", errors)
sys.exit(1 if errors else 0)
