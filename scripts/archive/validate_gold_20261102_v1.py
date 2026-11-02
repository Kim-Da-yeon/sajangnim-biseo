"""정답 라벨 검증 스크립트.

흐름: 라벨 JSON 읽기 → 필드·연산자 어휘 확인 → 근거 문구가 원문에 실제로 있는지 확인 → 쪽 번호 대조.
목적: 라벨 오타와 존재하지 않는 인용이 평가 지표를 오염시키는 일을 막는다.
결과 해석: 오류가 0건이면 형식과 인용만 통과한 것이며, 해석이 맞다는 뜻은 아니다.
"""
import json, os, re, sys

ROOT = os.path.expanduser("~/sosang_agent/data")
FIELDS = {"main_industry_ksic", "employees", "small_merchant", "small_craft_business", "revenue_prev_year", "revenue_3y_avg",
          "revenue_change_rate", "mfg_revenue", "business_status", "founded_date", "tax_arrears", "debt_default",
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
        q, p = norm(c["evidence"]["quote"]), c["evidence"]["page"]
        found = [k for k, v in pg.items() if q in v]
        if p not in found:
            print("인용 오류", c["id"], "기재쪽", p, "실제", found, c["evidence"]["quote"][:40]); errors += 1
    print(os.path.basename(path), "조건", len(g["conditions"]), "누적 오류", errors)
sys.exit(1 if errors else 0)
