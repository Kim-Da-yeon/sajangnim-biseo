"""평가용 정답 라벨 생성 스크립트.

흐름: 공고별 조건 라벨과 가상 프로필 사례를 정의 → data/labels/eval_*.json, eval_cases.json 저장.
목적: 시스템 출력을 보기 전에 정답을 코드로 고정해, 수정 이력을 파일 버전으로 추적한다.
결과 해석: 현재 AI 초안이며 참가자 확인 전이다. 프로필은 전부 가상이고, 정답은 공고 문구 기준 대조 결과이지 실제 자격 판단이 아니다.
"""
import json, os

OUT = os.path.expanduser("~/sosang_agent/data/labels")


def c(id, kind, field, op, value, page, quote, unit=None, basis="not_stated", group="AND", check="profile", exception=None, applies_to=None, waives=None):
    return dict(id=id, kind=kind, field=field, op=op, value=value, unit=unit, basis=basis, group=group, check=check,
                exception=exception, applies_to=applies_to, waives=waives or [], evidence=dict(page=page, quote=quote))


def ex(id, field, op, value, page, quote, basis="deadline_date", **k):
    # 제외 조건: 값이 입력 사용자 진술(declared)이며, 술어는 참이면 통과.
    return c(id, "exclusion", field, op, value, page, quote, basis=basis, check=k.pop("check", "declared"), **k)


NOTICES = {}

NOTICES["1068107"] = dict(source_text="1068107_브랜드점프업", scope="소상공인 신청 자격", conditions=[
    c("C1", "eligibility", "small_merchant", "derived", True, 3, "「소상공인기본법」제2조에따른소상공인"),
    c("C2", "eligibility", "business_status", "eq", "정상", 3, "정상영업중", basis="application_date"),
    c("C3", "eligibility", "own_brand", "eq", True, 3, "자사브랜드를보유한소상공인", basis="application_date"),
    ex("E1", "excluded_industry", "eq", False, 3, "소상공인 정책자금 융자제외 대상 업종은 신청 불가", basis="not_stated", check="profile"),
    ex("E2", "business_status", "not_in", ["휴업", "폐업", "부도"], 3, "접수 마감일 기준 기업이 휴·폐업 또는 부도 상태인 경우"),
    ex("E3", "tax_arrears", "eq", False, 3, "국세·지방세 체납", basis="not_stated"),
    ex("E4", "debt_default", "eq", False, 3, "금융기관 등 채무불이행", basis="not_stated"),
    ex("E5", "unfair_trade_1y", "eq", False, 3, "최근 1년 이내 공정거래법에 따른 불공정행위 위반", basis="not_stated", unit="최근 1년"),
    ex("E6", "product_origin", "not_in", ["해외 수입", "대기업"], 3, "해외 수입제품, 대기업 제품", basis="not_stated"),
    c("P1", "period", "application_period", "between", ["2026-05-11", "2026-05-29T18:00"], 4, "’26년5월11일(월) ~ 5월29일(금) 18시까지", basis="as_of_date"),
])

NOTICES["1069018"] = dict(source_text="1069018_판로추가", scope="소공인 신청 자격", conditions=[
    c("C1", "eligibility", "small_craft_business", "derived", True, 1, "판로개척및육성지원을희망하는소공인"),
    c("C2", "eligibility", "main_industry_ksic", "between", ["C10", "C34"], 1, "업종 코드 : ‘C10~C34’에 해당", unit="KSIC 중분류"),
    c("C3", "eligibility", "merchant_certificate", "eq", True, 1, "소상공인확인서 보유 必"),
    c("C4", "eligibility", "registration_includes_mfg", "eq", True, 1, "사업자등록증 상 ‘제조’ 포함"),
    c("C5", "eligibility", "mfg_revenue", "gt", 0, 1, "제조매출액 보유 必", unit="원"),
    c("C6", "eligibility", "support_field", "in", ["패션", "뷰티", "푸드"], 1, "지원분야관련판로개척"),
    c("C7", "eligibility", "domestic_site", "eq", True, 1, "대한민국 관할구역에 소재한 기업"),
    ex("E1", "business_status", "not_in", ["휴업", "폐업", "부도"], 1, "업체의 부도, 휴·폐업 중인 경우"),
    ex("E2", "tax_arrears", "eq", False, 1, "국세·지방세 체납"),
    ex("E3", "debt_default", "eq", False, 1, "금융기관 등의 채무불이행"),
    ex("E4", "gov_sanction", "eq", False, 1, "정부사업 참여제한(부정수급 등)"),
    ex("E5", "tops_selected_2026", "eq", False, 1, "‘26년 TOPS 선정 업체"),
    ex("E6", "founded_date", "lt", "2026-06-15", 1, "사업 공고일(‘26.6.15) 이후 창업한 업체", basis="notice_date", check="profile"),
    c("P1", "period", "application_period", "between", ["2026-06-15", "2026-06-19T18:00"], 2, "’26. 6. 15.(월) ~ 6. 19.(금) 18:00까지", basis="as_of_date"),
])

NOTICES["1069002"] = dict(source_text="1069002_스마트추가", scope="개별형", conditions=[
    c("C1", "eligibility", "small_craft_business", "derived", True, 1, "『도시형소공인지원에관한특별법』에따른소공인"),
    c("F1", "eligibility", "support_field", "eq", "공정기술", 2, "주조·금형·가공·용접등공정기술", group="OR:분야"),
    c("F2", "eligibility", "support_field", "in", ["패션", "뷰티", "식품", "리빙"], 3, "K-소비재4대중점분야(패션, 뷰티, 식품, 리빙)", group="OR:분야"),
    c("R1", "eligibility", "revenue_prev_year", "lt", 200000000, 2, "직전년도(’25년) 매출액2억원미만", unit="원", group="OR:매출"),
    c("R2", "eligibility", "revenue_3y_avg", "lt", 200000000, 2, "최근3개년연평균매출액2억원미만", unit="원", group="OR:매출"),
    ex("E1", "business_status", "not_in", ["휴업", "폐업", "부도"], 7, "업체의 부도, 휴·폐업 중인 경우"),
    ex("E2", "tax_arrears", "eq", False, 7, "국세·지방세 체납"),
    ex("E3", "debt_default", "eq", False, 7, "금융기관 등의 채무불이행"),
    ex("E4", "gov_sanction", "eq", False, 7, "정부사업 참여제한(부정수급 등)"),
    ex("E5", "prior_smart_benefit", "eq", False, 7, "소상공인시장진흥공단 스마트제조지원사업 수혜업체", unit="2024~2025년"),
    ex("E6", "prior_similar_benefit", "eq", False, 7, "스마트화지원사업 및 유사사업 수혜 업체"),
    ex("E7", "excluded_industry", "eq", False, 7, "도박·향락 등 불건전 업종", check="profile"),
    ex("E8", "other", "eq", "사치·투기 조장 우려 제조업 해당 여부", 7, "우려가 있다고 판단되는 제조업", check="discretionary"),
    ex("E9", "founded_date", "lt", "2026-01-01", 7, "2026.1.1. 이후 창업한 업체", check="profile"),
    c("P1", "period", "application_period", "between", ["2026-06-15", "2026-07-03T18:00"], 4, "2026년6월15일(월) ~ 7월3일(금) 18:00", basis="as_of_date"),
])

G, U = "일반경영안정자금", "긴급경영안정자금(일시적 경영애로)"
NOTICES["1071565"] = dict(source_text="1071565_정책자금변경5", scope=f"{G}, {U}", conditions=[
    c("C1", "eligibility", "small_merchant", "derived", True, 2, "소상공인기본법｣제2조및같은법시행령제3조의소상공인"),
    ex("L1", "tax_arrears", "eq", False, 4, "세금을체납중인소상공인", basis="not_stated", exception="압류·매각의 유예 등을 받은 소상공인은 직접대출에 한해 포함"),
    ex("L2", "credit_info_listed", "eq", False, 4, "“신용도판단정보”", basis="not_stated"),
    ex("L5", "business_status", "not_in", ["휴업", "폐업"], 4, "휴․폐업중인소상공인", basis="not_stated", exception="재해를 직접 원인으로 휴업 중이면 가동 중으로 간주"),
    ex("L6", "excluded_industry", "eq", False, 4, "정책자금융자제외업종", basis="not_stated", check="profile",
       exception="비주거용 건물 임대업(68112)은 일반경영안정자금에서 착한 임대인에 한해 허용"),
    ex("L7", "policy_loan_count_5y", "lt", 3, 4, "최근5년이내소상공인정책자금3회", basis="not_stated", unit="회",
       exception="특별경영안정자금 제외. 시설자금 또는 직접대출 성실상환자 1회 추가 가능"),
    c("U1", "eligibility", "revenue_change_rate", "le", -0.15, 8, "매출15% 이상감소한소상공인", group="OR:경영애로", applies_to=U),
    c("U2", "eligibility", "special_zone", "eq", True, 8, "매출감소확인예외", group="OR:경영애로", applies_to=U, waives=["U1"]),
])

NOTICES["1065100"] = dict(source_text="1065100_경영안정바우처", scope="지원 요건", conditions=[
    c("C1", "eligibility", "small_merchant", "derived", True, 1, "영업중인소상공인"),
    c("R1", "eligibility", "annualized_revenue", "gt", 0, 1, "연매출액0원초과1억400만원미만", unit="원"),
    c("R2", "eligibility", "annualized_revenue", "lt", 104000000, 1, "연매출액0원초과1억400만원미만", unit="원"),
    c("C2", "eligibility", "founded_date", "le", "2025-12-31", 2, "2025년12월31일이전"),
    c("C3", "eligibility", "business_status", "not_in", ["휴업", "폐업"], 2, "신청일기준휴‧폐업이아닌소상공인", basis="application_date"),
    ex("E1", "excluded_industry", "eq", False, 2, "소상공인정책자금융자제외업종", basis="not_stated", check="profile"),
    c("P1", "period", "application_period", "between", ["2026-02-09T09:00", "2026-12-18T18:00"], 3, "2월9일(월) 09시~ (잠정) 12월18일(금) 18시까지", basis="as_of_date", exception="종료일 잠정, 예산 소진 시 조기 마감 가능"),
])

NOTICES["PBLN127619"] = dict(source_text="PBLN127619_보은군소공인", scope="신청 자격", conditions=[
    c("C1", "eligibility", "region_site", "derived", "보은군", 1, "본사, 공장 중 1개 이상 보은군 소재", applies_to="기존 기업",
      exception="다른 문단은 '본사, 공장 또는 사업장'으로 표기. 사업장만 보은군이면 확인 필요"),
    c("C2", "eligibility", "main_industry_ksic", "eq", "C10", 1, "식료품 제조업(C10)을 영위하는 기업", applies_to="기존 기업", unit="KSIC 중분류"),
    c("C3", "eligibility", "employees", "lt", 10, 1, "상시근로자10인 미만의 소공인", unit="명", applies_to="기존 기업"),
    c("S1", "eligibility", "preparing_food_startup_in_region", "eq", True, 1, "보은군 관내 식품 제조 분야 창업을 준비하는 청년 및 예비창업자", applies_to="예비창업자"),
    c("S2", "eligibility", "can_start_within_3m", "eq", True, 1, "선정 이후 3개월 이내 창업", applies_to="예비창업자", check="declared"),
    ex("E1", "business_status", "not_in", ["휴업", "폐업"], 1, "휴업 또는 폐업 중인 기업", basis="not_stated", applies_to="기존 기업"),
    ex("E2", "tax_arrears", "eq", False, 1, "국세·지방세 또는4대보험료 체납", basis="not_stated"),
    ex("E3", "social_insurance_arrears", "eq", False, 1, "국세·지방세 또는4대보험료 체납", basis="not_stated"),
    ex("E4", "gov_sanction", "eq", False, 1, "지원사업 참여 제한 중인", basis="not_stated"),
    ex("E5", "prior_similar_benefit", "eq", False, 1, "금년도 유사 사업을 통하여 지원받은 기업", basis="not_stated", unit="금년도"),
    ex("E6", "other", "eq", "채무불이행·회생 등으로 사업수행이 어려운지", 1, "정상적인 사업수행이 어렵다고 판단", basis="not_stated", check="discretionary"),
    ex("E7", "other", "eq", "사업 목적 부합 여부", 1, "운영기관이 사업 목적에 부합하지 않는다고 판단", basis="not_stated", check="discretionary"),
    c("P1", "period", "application_period", "between", ["2026-10-22", "2026-11-05"], 1, "2026. 10. 22.(목) ~ 2026. 11. 5.(목)", basis="as_of_date",
      exception="절차 표의 모집공고 기간은 '10. 22.~10. 5.'로 표기돼 다름"),
])

A, B = "예비재창업자", "재창업기업"
NOTICES["1067425"] = dict(source_text="1067425_재도전추경", scope=f"{A}, {B} 신청 자격", conditions=[
    c("A1", "eligibility", "closure_history", "eq", True, 2, "사업 공고 직전일까지 중소기업을 폐업한 자", applies_to=A, basis="notice_date"),
    c("A2", "eligibility", "business_registration", "eq", False, 2, "공고일 기준 신청자 명의의 사업자등록 및 법인 등기가 없는 자", applies_to=A, basis="notice_date"),
    c("B1", "eligibility", "closure_history", "eq", True, 2, "중소기업을 폐업하고 새로운 중소기업을 설립", applies_to=B),
    c("B2", "eligibility", "restart_date", "ge", "2019-04-17", 2, "’19.4.17. 이후 재창업한 기업", applies_to=B, basis="notice_date"),
    c("B3", "eligibility", "head_office", "eq", True, 2, "지원대상은 본점(사) 기준", applies_to=B),
    ex("E1", "debt_default", "eq", False, 3, "채무불이행으로 규제 중인", exception="채무변제 증빙, 채무조정 합의, 회생·변제계획 인가, 면책 확정, 재기지원보증 등"),
    ex("E2", "tax_arrears", "eq", False, 3, "국세 또는 지방세 체납 중인", exception="강제징수·체납처분 유예, 특수채무 변제 증빙"),
    ex("E3", "recoup_outstanding", "eq", False, 3, "환수금등의 반환이 종결되지 않은", exception="전액 반환, 면책, 분할납부 정상 이행"),
    ex("E4", "startup_excluded_industry", "eq", False, 3, "창업에서 제외되는 업종", basis="not_stated", check="profile"),
    ex("E5", "prior_restart_program", "eq", False, 3, "[붙임2]에 명시된 사업에 선정되어 협약을 체결했던 이력", basis="not_stated"),
    ex("E6", "current_startup_program", "eq", False, 3, "창업사업화 지원사업", basis="not_stated", unit="2026년 중앙정부·공공기관"),
    ex("E7", "gov_sanction", "eq", False, 3, "창업지원사업에 참여 제한으로 제재 중인", basis="not_stated"),
    ex("E8", "business_status", "not_in", ["휴업", "폐업"], 3, "동 사업에 신청하는 사업자가 휴‧폐업 중인", basis="notice_date", applies_to=B),
    ex("E9", "other", "eq", "성실경영평가 통과 여부", 2, "성실경영평가", check="discretionary", basis="not_stated"),
])

# 사례 공통값: 지정하지 않은 항목은 "해당 없음(False)"을 입력한 상태. None으로 덮어쓰면 미입력이다.
BASE = dict(tax_arrears=False, debt_default=False, gov_sanction=False, business_status="정상", prior_similar_benefit=False)
FOOD = dict(BASE, main_industry_ksic="10799", industry_name="기타 식품 제조업", employees=4, revenue_3y_avg=300000000,
            founded_date="2020-03-02", merchant_certificate=True, registration_includes_mfg=True, mfg_revenue=300000000,
            support_field="푸드", domestic_site=True, tops_selected_2026=False, excluded_industry=False)
SHOP = dict(BASE, main_industry_ksic="47411", industry_name="의류 소매업", employees=3, revenue_3y_avg=500000000, founded_date="2019-05-10",
            excluded_industry=False, own_brand=True, unfair_trade_1y=False, product_origin="자체 제작")
FUND = dict(BASE, main_industry_ksic="56111", industry_name="한식 일반 음식점업", employees=3, revenue_3y_avg=400000000,
            founded_date="2021-01-04", excluded_industry=False, credit_info_listed=False, policy_loan_count_5y=1)
SMART = dict(BASE, main_industry_ksic="25112", industry_name="금속 가공 제품 제조업", employees=6, revenue_3y_avg=150000000,
             revenue_prev_year=150000000, founded_date="2018-07-01", support_field="공정기술", prior_smart_benefit=False, excluded_industry=False)
VOU = dict(SHOP, revenue_2025=80000000, founded_date="2019-05-10")
BOE = dict(BASE, applicant_type="기존 기업", main_industry_ksic="10799", employees=4, hq_region="보은군", factory_region="보은군", site_region="보은군",
           social_insurance_arrears=False)
RE = dict(tax_arrears=False, debt_default=False, gov_sanction=False, recoup_outstanding=False, startup_excluded_industry=False,
          prior_restart_program=False, current_startup_program=False)


def case(id, notice, as_of, profile, expected, period, decisive, reason, program=None, flags=None, **over):
    p = dict(profile)
    p.update(over)
    return dict(id=id, notice_id=notice, program=program, as_of=as_of, profile={k: v for k, v in p.items() if v is not None},
                expected=expected, period_status=period, decisive=decisive, reason=reason, flags=flags or [])


OK, NO, ASK = "일치", "불일치", "확인 필요"
IN, END, NA = "공고상 기간 내", "마감", "기간 미표기"
CASES = [
    # 브랜드 점프업: 음식점 5인 경계, 공통 제외 업종, 자사 브랜드
    case("BR1", "1068107", "2026-05-20", SHOP, OK, IN, [], "확인 가능한 조건 모두 통과"),
    case("BR2", "1068107", "2026-05-20", SHOP, NO, IN, ["C3"], "자사 브랜드 없음", own_brand=False),
    case("BR3", "1068107", "2026-05-20", SHOP, NO, IN, ["E1"], "일반 유흥 주점은 제외 업종", main_industry_ksic="56211", industry_name="일반 유흥 주점업", excluded_industry=None),
    case("BR4", "1068107", "2026-05-20", SHOP, ASK, IN, ["C3"], "자사 브랜드 미입력", own_brand=None),
    case("BR5", "1068107", "2026-05-20", SHOP, NO, IN, ["C1"], "음식점업 상시근로자 5명은 소상공인 기준(5명 미만) 초과", main_industry_ksic="56111", industry_name="한식 일반 음식점업", employees=5),
    case("BR6", "1068107", "2026-06-01", SHOP, ASK, END, ["E3"], "체납 여부 미입력, 기간은 마감", tax_arrears=None),
    # 판로개척: 10인 경계, 공고일 당일 창업 경계
    case("PA1", "1069018", "2026-06-17", FOOD, OK, IN, [], "확인 가능한 조건 모두 통과"),
    case("PA2", "1069018", "2026-06-17", FOOD, OK, IN, [], "제조업 상시근로자 9명은 10명 미만", employees=9),
    case("PA3", "1069018", "2026-06-17", FOOD, NO, IN, ["C1"], "상시근로자 10명은 소공인 기준 초과", employees=10),
    case("PA4", "1069018", "2026-06-17", FOOD, NO, IN, ["E5"], "2026년 TOPS 선정 업체", tops_selected_2026=True),
    case("PA5", "1069018", "2026-06-17", FOOD, NO, IN, ["E6"], "공고일 당일 창업은 '이후'에 포함", founded_date="2026-06-15"),
    case("PA6", "1069018", "2026-06-17", FOOD, ASK, IN, ["C3"], "소상공인확인서 보유 미입력", merchant_certificate=None),
    # 스마트제조 개별형: 매출 OR, 신생 기준, 재량 항목
    case("SM1", "1069002", "2026-06-20", SMART, OK, IN, [], "조건 통과, 재량 항목 표시 필요", flags=["기관 판단 표시"], revenue_3y_avg=250000000),
    case("SM2", "1069002", "2026-06-20", SMART, OK, IN, [], "직전년도 초과지만 3개년 평균 충족", flags=["기관 판단 표시"], revenue_prev_year=250000000, revenue_3y_avg=190000000),
    case("SM3", "1069002", "2026-06-20", SMART, NO, IN, ["R1", "R2"], "둘 다 2억 미만 아님(2억 정각 포함)", revenue_prev_year=200000000, revenue_3y_avg=210000000),
    case("SM4", "1069002", "2026-06-20", SMART, NO, IN, ["E9"], "2026.1.1. 창업은 '이후'에 포함", founded_date="2026-01-01"),
    case("SM5", "1069002", "2026-06-20", SMART, ASK, IN, ["R2"], "직전년도 초과, 3개년 평균 미입력", revenue_prev_year=250000000, revenue_3y_avg=None),
    case("SM6", "1069002", "2026-06-20", SMART, ASK, IN, ["E5"], "과거 스마트제조 수혜 여부 미입력", prior_smart_benefit=None),
    # 정책자금: 임대업 예외, 매출 감소와 면제
    case("PF1", "1071565", "2026-11-02", FUND, OK, NA, [], "일반경영안정자금 조건 통과", program=G),
    case("PF2", "1071565", "2026-11-02", FUND, NO, NA, ["L6"], "비주거용 건물 임대업, 착한 임대인 아님", program=G, main_industry_ksic="68112", industry_name="비주거용 건물 임대업", excluded_industry=None, good_landlord=False),
    case("PF3", "1071565", "2026-11-02", FUND, ASK, NA, ["L6"], "임대업 예외 해당 여부 미입력", program=G, main_industry_ksic="68112", industry_name="비주거용 건물 임대업", excluded_industry=None),
    case("PF4", "1071565", "2026-11-02", FUND, OK, NA, [], "매출 20% 감소", program=U, revenue_change_rate=-0.20),
    case("PF5", "1071565", "2026-11-02", FUND, NO, NA, ["U1", "U2"], "매출 10% 감소, 면제 지역 아님", program=U, revenue_change_rate=-0.10, special_zone=False),
    case("PF6", "1071565", "2026-11-02", FUND, OK, NA, [], "매출 10% 감소지만 상권활성화구역이라 매출 확인 면제", program=U, revenue_change_rate=-0.10, special_zone=True),
    # 바우처: 연 환산과 공고의 계산 예시
    case("VO1", "1065100", "2026-11-02", VOU, OK, IN, [], "2024년 이전 개업, 매출 8천만원", flags=["조기 마감 가능 표시"]),
    case("VO2", "1065100", "2026-11-02", VOU, OK, IN, [], "2025.10.20. 개업, 2,500만원÷3개월×12=1억원(공고 예시)", flags=["조기 마감 가능 표시"], founded_date="2025-10-20", revenue_2025=25000000),
    case("VO3", "1065100", "2026-11-02", VOU, NO, IN, ["R2"], "2,700만원÷3개월×12=1억 800만원", flags=["조기 마감 가능 표시"], founded_date="2025-10-20", revenue_2025=27000000),
    case("VO4", "1065100", "2026-11-02", VOU, NO, IN, ["R2"], "1억 400만원 정각은 미만 아님", flags=["조기 마감 가능 표시"], revenue_2025=104000000),
    case("VO5", "1065100", "2026-11-02", VOU, NO, IN, ["C2"], "2026년 개업", flags=["조기 마감 가능 표시"], founded_date="2026-01-02", revenue_2025=None),
    case("VO6", "1065100", "2026-11-02", VOU, ASK, IN, ["R1", "R2"], "2025년 매출 미입력", flags=["조기 마감 가능 표시"], revenue_2025=None),
    # 보은군: 표기 충돌, 유형 분기
    case("BE1", "PBLN127619", "2026-11-02", BOE, OK, IN, [], "기존 기업 조건 통과", flags=["일정 표기 불일치 표시", "기관 판단 표시"]),
    case("BE2", "PBLN127619", "2026-11-02", BOE, NO, IN, ["C2"], "의복 제조업은 C10 아님", flags=["일정 표기 불일치 표시"], main_industry_ksic="14191"),
    case("BE3", "PBLN127619", "2026-11-02", BOE, NO, IN, ["C1"], "소재지 전부 청주시", flags=["일정 표기 불일치 표시"], hq_region="청주시", factory_region="청주시", site_region="청주시"),
    case("BE4", "PBLN127619", "2026-11-02", BOE, ASK, IN, ["C1"], "사업장만 보은군, 공고 내 표기가 달라 판단 불가", flags=["일정 표기 불일치 표시", "근거 충돌 표시"], hq_region="청주시", factory_region="청주시"),
    case("BE5", "PBLN127619", "2026-11-02", BOE, NO, IN, ["E3"], "4대보험료 체납", flags=["일정 표기 불일치 표시"], social_insurance_arrears=True),
    case("BE6", "PBLN127619", "2026-11-02", BASE, ASK, IN, ["S2"], "예비창업자, 3개월 내 창업 가능 여부 미입력", flags=["일정 표기 불일치 표시"], applicant_type="예비창업자", preparing_food_startup_in_region=True, business_status=None, social_insurance_arrears=False),
    # 재도전: 유형 분기, 7년 경계, 예외 미상
    case("RE1", "1067425", "2026-04-25", RE, OK, IN, [], "폐업 이력 있고 현재 사업자등록 없음", flags=["기관 판단 표시"], applicant_type=A, closure_history=True, business_registration=False),
    case("RE2", "1067425", "2026-04-25", RE, OK, IN, [], "2020년 재창업", flags=["기관 판단 표시"], applicant_type=B, closure_history=True, restart_date="2020-06-01", head_office=True, business_status="정상"),
    case("RE3", "1067425", "2026-04-25", RE, NO, IN, ["B2"], "2019.4.16. 재창업은 기준일 이전", applicant_type=B, closure_history=True, restart_date="2019-04-16", head_office=True, business_status="정상"),
    case("RE4", "1067425", "2026-04-25", RE, NO, IN, ["A2"], "예비재창업자인데 사업자등록 보유", applicant_type=A, closure_history=True, business_registration=True),
    case("RE5", "1067425", "2026-04-25", RE, ASK, IN, ["E1"], "채무불이행 있음, 예외 해당 여부 미입력", applicant_type=A, closure_history=True, business_registration=False, debt_default=True),
    case("RE6", "1067425", "2026-04-25", RE, NO, IN, ["E5"], "붙임2 사업 협약 이력 있음", applicant_type=A, closure_history=True, business_registration=False, prior_restart_program=True),
]

for nid, n in NOTICES.items():
    n.update(notice_id=nid, labeler="AI 초안", status="참가자 확인 전")
    json.dump(n, open(f"{OUT}/eval_{nid}.json", "w"), ensure_ascii=False, indent=1)
json.dump(dict(status="AI 초안, 참가자 확인 전", note="프로필은 전부 가상", cases=CASES), open(f"{OUT}/eval_cases.json", "w"), ensure_ascii=False, indent=1)
from collections import Counter
print("조건", sum(len(n["conditions"]) for n in NOTICES.values()), "사례", len(CASES), Counter(x["expected"] for x in CASES))
