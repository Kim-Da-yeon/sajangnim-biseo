"""새 공고(holdout3) 5건의 정답 라벨 작성 스크립트.

흐름: 공고별 조건 정의 → 범위 정의 → 사례 30개 정의 → 인용 문구가 표시 쪽에 있는지 확인 → JSON 저장.
목적: 시스템 출력과 독립적으로, 공고 원문만 읽고 정한 정답을 평가 전에 고정한다.
결과 해석: 파일은 AI 초안이며 참가자 확인 전이다. 인용 확인 통과는 문구 존재만 보장하고 해석의 옳음은 보장하지 않는다.
  판정기 점검(src/check_holdout3_20261102_v1.py)의 불일치는 라벨을 맞추는 신호가 아니라 보고 대상이다.

라벨 작성 원칙.
- 기준서 v7을 따른다. 어휘에 없는 요건은 field=other로 두고, 기관 재량이면 discretionary, 사실 요건이면 unsupported.
- expected는 공고를 읽은 사람의 판단이다. unsupported 요건도 프로필 other 문장으로 사실이 확인되면 충족·위반을 판단한다.
  그래서 unsupported 요건이 남은 공고의 일치·불일치 사례는 판정기가 확인 필요로 낼 수 있다.
- 인용은 쪽 원문의 한 줄 안에서 글자 그대로 잡는다. 저장 전에 원문 부분 문자열인지 코드로 확인한다.
- 프로필 보조 키: other, {field}_exception, applicant_type, industry_name.
- 참가자 확인 원칙: '이후'는 당일 포함, 표기가 갈리는 소재지 등은 넓게 적힌 쪽 인정, 공고의 제외 조건을 사장님이 확인할 수 없으면 확인 필요,
  적힌 업종에 부수적으로 해당해도 불일치.

해석 메모(JSON에는 조건별 note 키를 두지 않으므로 여기에 남긴다).
- PBLN127480 R1: 1쪽은 '연매출액'만, 6쪽 담당공무원 확인사항은 '2025년도 연매출액'이다. 연도가 적힌 6쪽을 근거로 revenue_prev_year로 둔다.
  2025년 중 개업의 연 환산 규정은 없다.
- PBLN127480 '영업 중인'은 X4(휴·폐업 제외)와 같은 판단이라 조건을 늘리지 않는다.
- PBLN127480 X2: 타 시·군·구 이전 제외는 공고일 현재 동해시 소재(S1)와 사실상 같으나 공고의 별도 항목이라 그대로 둔다.
- PBLN127480: 지방세 납세증명서를 제출하지만 체납 제외 문구는 없다. 요건으로 세우지 않고 out_of_scope에 둔다. 참가자 확인 항목이다.
- PBLN127480 X1: '이미 받았거나'에 기간 제한이 없다. 기간을 추정하지 않고, 유사 사업 해당 여부를 모르는 사례는 확인 필요로 둔다.
- PBLN127233 N1: 신청지역 목록이 거주지 기준인지 사업장 기준인지 적혀 있지 않다. 6쪽의 '신청 시 거주지 시·군 예산'은 거주지를 시사하지만 단정할 수 없어 unsupported다.
- PBLN127233 R2: 연 매출액의 연도가 없어 annualized_revenue로 둔다. 2025년으로 추정하지 않는다.
- PBLN127233 Y1: '출산일 기준 1년 전에 사업장을 운영'은 출산일 1년 전 시점에 운영 중이라는 뜻으로 읽었다.
- PBLN127233 H1: 대체인력 요건이지만 7쪽이 '신청요건 및 지원요건을 충족한' 자를 선정한다고 적어 조건으로 둔다.
  선정 통보 후 출산 12개월 전까지 6개월이 남지 않으면 위반으로 읽었다. 참가자 확인 항목이다.
- PBLN127233 X11: 붙임 목록은 다른 공고와 다르다(63992·91242·68224 없음, 5821 대신 5812, 75330에 '중' 없음, 91136 허용 명시).
  제외 업종에 들어도 '신청건별 시·군 협의'가 있어 예외 여부 불명으로 보고 확인 필요로 둔다. D2가 X11을 면제할 수 있다.
- PBLN127568 X4: 표에 '소상공인 정책자금 지원 제외 업종'이라고만 있고 목록이 없다. 기준서 8장의 정책자금 별표1과 같은 목록으로 보고 profile로 둔다.
  기준서 3장 '문서가 없으면 unsupported'로 읽는 해석도 가능해 참가자 확인 항목이다.
- PBLN127568 L3: 원문은 '광주·전남·제주'다. 판정 대조를 위해 정식 행정구역명으로 적는다. 붙임 3의 '전북'은 동의서 서식 잔재로 보고 소재지로 쓰지 않는다.
- PBLN127568 통신판매업 신고증: 제출서류 목록에만 있고 요건 문구가 없어 out_of_scope다. 참가자 확인 항목이다.
- PBLN127568 X5: '관리식품 등'은 공고에 정의가 없다. 건강기능식품 인증품은 위반, 관리식품 해당이 불명이면 확인 필요로 판단한다.
- 1065812: 자사 브랜드는 신청 요건이 아니다(2단계 진출 요건). X8의 단순 유통 제외만 조건으로 둔다.
- 1065812 C3: 모집규모의 4대 분야를 support_field로 옮겼다. 분야 정의가 없어 4대 분야 밖으로 단정하기 어려운 품목은 확인 필요다.
- 1065812 재해자금 예외 표는 재해자금 융자에 대한 것이라 이 사업의 예외로 쓰지 않는다.
- 1065016 F1: 유형 비교표 각주는 '7년 미만', 사업개요·신청자격은 '7년 이내'이고 세부 조건은 2019.1.23.부터다.
  표기가 갈리면 넓은 쪽 인정 원칙과 세부 조건의 명시 날짜에 따라 충돌로 두지 않고 2019-01-23 포함으로 둔다.
- 1065016 F2·FT1: 신산업·패스트트랙은 applies_to로 분리해 해당 기업에서만 업력 OR 대안이 된다.
- 1065016 FT2: '고용인원(대표자 제외)'을 employees로 옮겼다. 상시근로자와 산정이 완전히 같은지는 공고에 없다.
- 1065016 E1~E3: 예외 항목만 마감일 기준이고 제외 항목 자체의 기준일은 없어 not_stated다. E9만 신청일 기준이다.
- 1065016: 원문은 쪽 표시가 [[p1]] 하나뿐이다(1065812도 같음). 모든 근거가 page=1이다.
- 1065016 권역 외 주관기관 신청은 '제외될 수 있음'이고 신청 절차 항목이라 out_of_scope다.
"""
import json
import os
import sys

ROOT = os.path.expanduser("~/sosang_agent/data")
LABELS = f"{ROOT}/labels"
LABELER, STATUS = "AI 초안", "참가자 확인 전"
AGENCY = "기관 판단 표시"
EARLY = "조기 마감 가능 표시"
BEFORE, IN_PERIOD, CLOSED, UNKNOWN = "접수 전", "공고상 기간 내", "마감", "일정 확인 필요"
OK, NO, ASK = "일치", "불일치", "확인 필요"
WON = "원"


def cond(id, kind, field, op, value, basis, page, quote, group="AND", check="profile", unit=None,
         exception=None, applies_to=None, waives=None):
    # 기준서 3장의 조건 스키마 한 건. 술어는 참이면 통과하는 방향으로 적는다.
    return {"id": id, "kind": kind, "field": field, "op": op, "value": value, "unit": unit, "basis": basis,
            "group": group, "check": check, "exception": exception, "applies_to": applies_to,
            "waives": waives or [], "evidence": {"page": page, "quote": quote}}


def other(id, kind, value, page, quote, check="unsupported", group="AND", exception=None, applies_to=None,
          basis="not_stated", waives=None):
    # 어휘로 담지 못하는 요건. value는 묻는 내용을 글로 적는다.
    return cond(id, kind, "other", "eq", value, basis, page, quote, group, check, None, exception, applies_to, waives)


def case(id, notice_id, as_of, profile, expected, period, decisive, reason, flags):
    return {"id": id, "notice_id": notice_id, "program": None, "as_of": as_of, "profile": profile, "expected": expected,
            "period_status": period, "decisive": decisive, "reason": reason, "flags": list(flags)}


# ---------- 1. 동해시 카드수수료 (PBLN127480) ----------
# 공고일(2026-10-26) 기준 소재·영업, 2025년 매출 3억 이하, 제외 업종 붙임 1. 접수가 11.9. 시작이라 11.2. 기준은 접수 전이다.
DH_X3_EX = ("다단계판매 등록 영위, 부동산관리업(6821), 신청일 기준 동일 장소 6개월 이상 부동산 중개·대리업(68221)·분양 대행업(68224), "
            "비거주용건물임대업(68112) 중 공유오피스·공유주방, 유사의료업(86902), 안마원(96122), 시각장애인 운영 안마원·안마시술소는 신청 가능")
c_dh = [
    cond("M1", "eligibility", "small_merchant", "derived", True, "not_stated", 1,
         "▶ 「소상공인기본법」 및 「소상공인 보호 및 지원에 관한 법률」에 따른 소상공인"),
    cond("R1", "eligibility", "revenue_prev_year", "le", 300000000, "not_stated", 6, "2025년도 연매출액 3억원 이하 여부 확인", unit=WON),
    cond("S1", "eligibility", "site_region", "eq", "동해시", "notice_date", 1, "공고일 현재 동해시에 사업장을"),
    cond("A1", "eligibility", "single_application", "eq", True, "not_stated", 2, "- 대표자 1인당 한 사업장만 신청 가능합니다.",
         check="declared", applies_to="다수 사업체 대표"),
    cond("A2", "eligibility", "joint_rep_main", "eq", True, "not_stated", 2, "- 공동대표일 경우 협의 후 위임대표가 한 사업장만 신청 가능합니다.",
         check="declared", applies_to="공동대표 사업장"),
    cond("X1", "exclusion", "prior_similar_benefit", "eq", False, "not_stated", 1, "- 동일 사업 또는 유사한 목적의 사업으로 카드수수료 지원을 이미",
         check="declared"),
    cond("X2", "exclusion", "site_region", "eq", "동해시", "notice_date", 1, "- 공고일 기준 사업장을 타 시・군・구로 이전한 업체"),
    cond("X3", "exclusion", "excluded_industry", "eq", False, "not_stated", 1, "- 소상공인 정책자금 융자제외 대상 업종을 영위하는 업체 [붙임 1]",
         exception=DH_X3_EX),
    cond("X4", "exclusion", "business_status", "not_in", ["휴업", "폐업"], "notice_date", 1, "- 공고일 현재 휴업 또는 폐업 중인 업체"),
    cond("P1", "period", "application_period", "between", ["2026-11-09", "2026-11-13T18:00"], "as_of_date", 2,
         "○ 신청기간 : 2026. 11. 9.(월) ~ 11. 13.(금) 18:00까지", exception="예산 소진 시 조기 마감될 수 있음. 점심시간 12:00~13:00 제외"),
]
oos_dh = [
    {"text": "2025년 카드매출액의 0.5%, 업체당 최대 20만원", "reason": "자격이 아니라 지원 내용"},
    {"text": "지방세 납세증명서, 통장사본 등 제출서류와 계좌 명의 확인", "reason": "서류 확인 항목으로 체납 제외 등 요건 문구가 없음"},
    {"text": "기한 내 보완요청 미응답 시 제외, 허위 신청 환수", "reason": "자격이 아니라 신청 절차와 사후 조치"},
]


def dh(**k):
    p = {"main_industry_ksic": "56111", "industry_name": "한식 일반 음식점업", "employees": 4, "revenue_3y_avg": 200000000,
         "revenue_prev_year": 200000000, "site_region": "강원특별자치도 동해시", "business_status": "정상",
         "prior_similar_benefit": False, "other": "제 사업장은 이곳 하나입니다. 다른 곳으로 옮긴 적이 없습니다."}
    p.update(k)
    return p


DH_F = (EARLY,)
cases_dh = [
    case("DH1", "PBLN127480", "2026-11-02", dh(revenue_prev_year=300000000), OK, BEFORE, [],
         "2025년 매출 3억원 정각은 '이하'에 포함, 서비스업 4명은 5명 미만. 접수 시작 전", DH_F),
    case("DH2", "PBLN127480", "2026-11-13",
         dh(main_industry_ksic="10712", industry_name="빵류 제조업", employees=9, revenue_prev_year=250000000, joint_rep_main=True,
            applicant_type="공동대표 사업장", other="공동대표 사업장이고 협의해서 제가 위임대표로 이 사업장만 신청합니다. 다른 곳으로 옮긴 적이 없습니다."),
         OK, IN_PERIOD, [], "제조업 9명은 10명 미만, 공동대표는 위임대표 신청. 마감일 당일은 기간 내", DH_F),
    case("DH3", "PBLN127480", "2026-11-10", dh(revenue_prev_year=301000000, revenue_3y_avg=290000000), NO, IN_PERIOD, ["R1"],
         "2025년 매출이 3억원 초과. 3년 평균은 기준이 아니다", DH_F),
    case("DH4", "PBLN127480", "2026-11-02",
         dh(main_industry_ksic="96112", industry_name="두발 미용업", employees=5), NO, BEFORE, ["M1"],
         "그 밖의 업종 5명은 '5명 미만' 위반", DH_F),
    case("DH5", "PBLN127480", "2026-11-02",
         {**{k: v for k, v in dh().items() if k != "prior_similar_benefit"},
          "other": "제 사업장은 이곳 하나입니다. 올해 초 다른 기관에서 카드 수수료 관련 지원을 받은 것 같은데 같은 목적의 사업인지 잘 모르겠습니다."},
         ASK, BEFORE, ["X1"], "유사 목적 카드수수료 지원 해당 여부를 사장님이 확인 못 함", DH_F),
    case("DH6", "PBLN127480", "2026-11-10",
         dh(main_industry_ksic="68221", industry_name="부동산 중개 및 대리업", employees=3,
            other="부동산 중개사무소입니다. 지금 자리로 옮긴 날짜를 아직 찾아보지 못했습니다."),
         ASK, IN_PERIOD, ["X3"], "부동산업은 제외지만 68221은 동일 장소 6개월 이상이면 가능. 기간 값 없음", DH_F),
]

# ---------- 2. 경북 아이보듬 (PBLN127233) ----------
# 출산·경북 거주지와 사업장·신청지역·사업장 운영 기간·매출, 제외 항목 다수. 종료일이 없어 기간은 일정 확인 필요.
IB_X11_EX = ("부동산관리업(6821), 동일 장소 6개월 이상 중개·대리업(68221), 공유오피스·공유주방(68112), 유사의료업(86902), "
             "골프연습장·스크린골프연습장(91136), 시각장애인 운영 안마원·안마시술소는 가능. 그 밖의 제외 업종도 신청건별 시·군 협의로 지원 가능 여부 검토")
c_ib = [
    other("B1", "eligibility", "2026.1.1.~12.31. 본인 또는 배우자 출산", 3, "□(자격) 2026. 1. 1. ~ 12. 31.내에 출산한 소상공인 및 배우자 중"),
    cond("M1", "eligibility", "small_merchant", "derived", True, "not_stated", 3, "①소상공인(「소상공인 보호 및 지원에 관한 법률」제2조에 따른 소상공인 사업자)"),
    other("G1", "eligibility", "거주지 주소 경북", 3, "②거주지 및 사업장 주소가 모두 경북에 두고 있을 것"),
    cond("G2", "eligibility", "site_region", "eq", "경상북도", "not_stated", 3, "②거주지 및 사업장 주소가 모두 경북에 두고 있을 것"),
    other("N1", "eligibility", "신청지역(안동·구미·영천·경산·영양·영덕·성주·예천·울릉) 소재. 거주지·사업장 중 어느 기준인지 미기재", 1, "○안동, 구미, 영천, 경산, 영양, 영덕, 성주, 예천, 울릉"),
    other("Y1", "eligibility", "출산일 1년 전 시점에 사업장 운영", 3, "③출산일 기준 1년 전에 사업장을 운영하고 있어야 하며 연 매출액이 12백만원이상일 것"),
    cond("R2", "eligibility", "annualized_revenue", "ge", 12000000, "not_stated", 3, "③출산일 기준 1년 전에 사업장을 운영하고 있어야 하며 연 매출액이 12백만원이상일 것", unit=WON),
    other("K1", "eligibility", "사업기간 내 사업장·거주지 주소 유지", 3, "④사업장 및 거주지 주소는 사업기간 내 유지"),
    other("H1", "eligibility", "선정 통보 다음날부터 출산 후 12개월 전까지 연속 6개월 대체인력 고용 가능", 4, "12개월 전까지 연속된 6개월기간 고용"),
    other("X1", "exclusion", "본인 또는 법인 명의 통장 입출금 거래 가능", 3, "- 본인 및 법인명의의 통장 입출금 거래가 불가능한 사업자"),
    cond("X2", "exclusion", "misuse_history", "eq", False, "not_stated", 3, "- 허위 또는 부정한 방법으로 신청한 사업자", check="declared"),
    cond("X3", "exclusion", "tax_arrears", "eq", False, "not_stated", 3, "- 국세·지방세 체납 중인 사업자", check="declared"),
    cond("X4", "exclusion", "business_status", "not_in", ["휴업", "폐업"], "not_stated", 3, "- 휴·폐업 중인 사업자 및 무점포 사업자"),
    other("X5", "exclusion", "점포 있음(무점포 사업자 아님)", 3, "- 휴·폐업 중인 사업자 및 무점포 사업자"),
    cond("X6", "exclusion", "prior_similar_benefit", "eq", False, "not_stated", 3, "- 본인 또는 배우자가 출산과 관련하여 경영지원 인건비를 지원받고 있는 소상공인",
         check="declared", exception="수혜기간 및 타 지원사업의 인건비 지원대상이 다른 경우 지원 가능(5쪽)"),
    cond("X7", "exclusion", "multiple_business_applying", "eq", False, "not_stated", 3, "- 부부 각각의 사업장이 있을 경우 중복지원 불가", check="declared"),
    other("X8", "exclusion", "최근 1년 이내 임금체불 사업장 아님", 3, "- 최근 1년 이내 임금체불사업장, 중대재해발생업체, 고용지원금 부정수급 발생 사업장"),
    other("X9", "exclusion", "최근 1년 이내 중대재해 발생 업체 아님", 3, "- 최근 1년 이내 임금체불사업장, 중대재해발생업체, 고용지원금 부정수급 발생 사업장"),
    other("X10", "exclusion", "최근 1년 이내 고용지원금 부정수급 사업장 아님", 3, "- 최근 1년 이내 임금체불사업장, 중대재해발생업체, 고용지원금 부정수급 발생 사업장"),
    other("X12", "exclusion", "최근 1년 이내 최저임금법 위반 없음", 5, "부정수급, 최저임금법 위반 등 이에 준하는 사항이 있을 시 선정 제외"),
    cond("X11", "exclusion", "excluded_industry", "eq", False, "not_stated", 3, "- 지원제외 대상 업종 ※ 붙임 참조", exception=IB_X11_EX),
    other("D1", "exclusion", "기타 위에 준하는 사항", 3, "- 기타 위에 준하는 사항이 확인되었을 경우", "discretionary"),
    other("D2", "eligibility", "제외 업종의 신청건별 시·군 협의 결과", 3, "* 지원제외 대상 업종 중 신청건별로 해당 시·군과 협의하여 지원가능 여부 검토",
          "discretionary", waives=["X11"]),
    other("D3", "eligibility", "자격심사 결과(접수순서, 적격여부, 예산범위)", 2, "자격심사(접수순서, 적격여부, 예산범위 등)", "discretionary"),
    cond("P1", "period", "application_period", "between", ["2026-10-14", None], "as_of_date", 1, "○2026.10.14.(수) ~ 예산소진시까지* 예산소진시조기마감",
         exception="예산 소진 시 조기 마감. 확정 종료일 없음. 선정 후에도 예산 소진 시 지급 제한 가능"),
]
oos_ib = [
    {"text": "월 최대 2백만원, 연속 6개월 인건비", "reason": "자격이 아니라 지원 내용"},
    {"text": "대체인력 근로계약·최저임금 준수·4대보험, 선정 통보 후 2개월 내 채용, 다태아도 1명", "reason": "선정 후 대체인력 고용 의무. 신청 시점에 대조할 값이 없음"},
    {"text": "신청서, 증빙서류, 앱 접수, 지원금 청구, 현장점검, 심의위원회 지급중단", "reason": "신청 절차와 선정 후 사후 관리"},
]

IB_OTHER = ("{birth} 지금 거주지와 사업장 주소가 모두 {region}이고 사업기간 동안 옮길 계획이 없습니다. 점포를 운영하고 있습니다. "
            "제 이름의 통장으로 입출금이 됩니다. {since} 선정 통보를 받으면 바로 대체인력을 구해 6개월 연속 고용할 수 있습니다. "
            "최근 1년 안에 임금체불, 중대재해, 고용지원금 부정수급, 최저임금법 위반은 없었습니다.")


def ib(birth="올해 9월 20일에 제가 출산했습니다.", region="안동", since="2022년부터 가게를 운영했습니다.", **k):
    p = {"main_industry_ksic": "47412", "industry_name": "여성용 겉옷 소매업", "employees": 1, "revenue_3y_avg": 50000000,
         "annualized_revenue": 50000000, "site_region": "경상북도 안동시", "business_status": "정상", "tax_arrears": False,
         "misuse_history": False, "prior_similar_benefit": False, "multiple_business_applying": False,
         "other": IB_OTHER.format(birth=birth, region=region, since=since)}
    p.update(k)
    return p


IB_F = (AGENCY, EARLY)
cases_ib = [
    case("IB1", "PBLN127233", "2026-11-02", ib(annualized_revenue=12000000, revenue_3y_avg=12000000), OK, UNKNOWN, [],
         "연 매출 1,200만원 정각은 '이상'에 포함. 2026년 9월 출산, 6개월 고용 기간 남음", IB_F),
    case("IB2", "PBLN127233", "2026-11-02",
         ib(birth="올해 10월 1일에 아내가 출산했습니다. 아내는 사업장이 없습니다.", region="구미", main_industry_ksic="91136",
            industry_name="골프연습장 운영업", site_region="경상북도 구미시", employees=2, annualized_revenue=80000000, revenue_3y_avg=80000000),
         OK, UNKNOWN, [], "배우자 출산 포함. 91136 스크린골프연습장은 9쪽에 지원가능으로 명시", IB_F),
    case("IB3", "PBLN127233", "2026-11-02", ib(annualized_revenue=11900000, revenue_3y_avg=11900000), NO, UNKNOWN, ["R2"],
         "연 매출 1,190만원은 1,200만원 미만", IB_F),
    case("IB4", "PBLN127233", "2026-11-02", ib(birth="2025년 12월 31일에 제가 출산했습니다."), NO, UNKNOWN, ["B1"],
         "2025-12-31 출산은 2026.1.1. 시작 전. 출산 후 12개월 전까지 6개월도 남지 않음", IB_F),
    case("IB5", "PBLN127233", "2026-11-02",
         ib(other=IB_OTHER.format(birth="올해 9월 20일에 제가 출산했습니다.", region="경북", since="2022년부터 가게를 운영했습니다.")
            + " 사업장은 안동이고 집은 포항입니다."),
         ASK, UNKNOWN, ["N1"], "사업장은 신청지역이나 거주지는 아님. 신청지역이 어느 주소 기준인지 공고에 없음", IB_F),
    case("IB6", "PBLN127233", "2026-11-02",
         ib(main_industry_ksic="68111", industry_name="주거용 건물 임대업"), ASK, UNKNOWN, ["X11"],
         "68은 제외 업종이고 해당 예외가 없으나 신청건별 시·군 협의 단서가 있어 결과를 알 수 없음", IB_F),
]

# ---------- 3. 동행축제 라이브커머스 (PBLN127568) ----------
# 소상공인확인서와 유효기간, 사업자등록 소재지, 소비재 완제품, 제외 품목 표. 평가위원회 선정은 재량이다.
c_lc = [
    cond("M1", "eligibility", "small_merchant", "derived", True, "not_stated", 2, "◦(대상) 소비재 완제품을 취급하는 소상공인"),
    other("L4", "eligibility", "소비재 완제품 취급", 2, "◦(대상) 소비재 완제품을 취급하는 소상공인"),
    cond("L3", "eligibility", "site_region", "in", ["광주광역시", "전라남도", "제주특별자치도"], "not_stated", 2, "◦(자격) 사업자등록증 소재지가 광주·전남·제주지역인 소상공인"),
    cond("L1", "eligibility", "merchant_certificate", "eq", True, "not_stated", 2, "* 소상공인확인서 발급 必"),
    other("L5", "eligibility", "소상공인확인서 유효기간 2026.4.1.~2027.3.31.", 2, "* 유효기간 2026.4.1 ~ 2027.3.31. 확인서만 인정"),
    cond("X1", "exclusion", "tax_arrears", "eq", False, "not_stated", 2, "◦국세·지방세를 체납 중인 경우", check="declared"),
    cond("X2", "exclusion", "product_origin", "not_in", ["대기업 프랜차이즈 제품", "중견기업 프랜차이즈 제품"], "not_stated", 2, "∘ 대기업 및 중견기업 프랜차이즈 제품"),
    cond("X3", "exclusion", "product_origin", "not_in", ["수입제품", "대기업 유통판매 업체 제품"], "not_stated", 2, "∘ 수입제품 또는 대기업 유통판매 업체 제품"),
    cond("X4", "exclusion", "excluded_industry", "eq", False, "not_stated", 2, "∘ 소상공인 정책자금 지원 제외 업종"),
    other("X5", "exclusion", "건강기능식품·관리식품 등이 아닌 제품", 2, "∘ 건강기능식품 및 관리식품 등"),
    other("D1", "eligibility", "평가위원회의 우수성·적합성·경쟁력 평가", 3, "위원회를 개최하여 우수성, 적합성, 경쟁력 등을 기준으로 선정", "discretionary"),
    cond("P1", "period", "application_period", "between", ["2026-10-29", "2026-11-05T18:00"], "as_of_date", 2,
         "◦(모집기간) ’26. 10. 29.(목) ~ ‘26. 11. 5.(목) 18:00까지"),
]
oos_lc = [
    {"text": "촬영 스튜디오·쇼호스트·방송 송출", "reason": "자격이 아니라 지원 내용"},
    {"text": "통신판매업 신고증, 납세증명서 등 제출서류", "reason": "제출서류 목록에만 있고 요건 문구가 없음. 신고증 필수 여부는 참가자 확인 항목"},
    {"text": "교환·환불 직접 대응, 매출 등 정보제공 협조", "reason": "선정 후 의무"},
]


def lc(**k):
    p = {"main_industry_ksic": "20423", "industry_name": "화장비누 제조업", "employees": 3, "revenue_3y_avg": 120000000,
         "merchant_certificate": True, "site_region": "전라남도 순천시", "tax_arrears": False, "product_origin": "자사 제조 제품",
         "other": "직접 만든 수제 비누를 완제품으로 팝니다. 소상공인확인서 유효기간은 2026년 4월 1일부터 2027년 3월 31일까지입니다. 건강기능식품이나 관리식품은 다루지 않습니다."}
    p.update(k)
    return p


LC_F = (AGENCY,)
cases_lc = [
    case("LC1", "PBLN127568", "2026-11-02", lc(), OK, IN_PERIOD, [], "전남 소재, 유효기간 맞는 확인서, 자사 소비재 완제품", LC_F),
    case("LC2", "PBLN127568", "2026-11-05",
         lc(main_industry_ksic="10301", industry_name="과실 및 채소 절임식품 제조업", employees=9, site_region="제주특별자치도 제주시",
            other="직접 만든 감귤 잼을 병에 담아 완제품으로 팝니다. 소상공인확인서 유효기간은 2026년 4월 1일부터 2027년 3월 31일까지입니다. 건강기능식품이나 관리식품은 아닙니다."),
         OK, IN_PERIOD, [], "제주는 공고 소재지에 명시, 제조업 9명은 10명 미만, 마감일 당일은 기간 내", LC_F),
    case("LC3", "PBLN127568", "2026-11-02",
         lc(main_industry_ksic="10712", industry_name="빵류 제조업", site_region="경기도 광주시",
            other="직접 구운 빵을 포장해 완제품으로 팝니다. 소상공인확인서 유효기간은 2026년 4월 1일부터 2027년 3월 31일까지입니다. 건강기능식품이나 관리식품은 아닙니다."),
         NO, IN_PERIOD, ["L3"], "경기도 광주시는 광주광역시가 아님", LC_F),
    case("LC4", "PBLN127568", "2026-11-02",
         lc(main_industry_ksic="47813", industry_name="화장품 소매업", site_region="광주광역시 남구", product_origin="수입제품",
            other="해외에서 수입한 화장품을 완제품으로 팝니다. 소상공인확인서 유효기간은 2026년 4월 1일부터 2027년 3월 31일까지입니다."),
         NO, IN_PERIOD, ["X3"], "수입제품은 취급 불가 품목", LC_F),
    case("LC5", "PBLN127568", "2026-11-02",
         lc(other="직접 만든 수제 비누를 완제품으로 팝니다. 소상공인확인서는 있는데 유효기간이 언제까지인지 지금은 확인이 안 됩니다. 건강기능식품이나 관리식품은 다루지 않습니다."),
         ASK, IN_PERIOD, ["L5"], "확인서 유효기간 값 없음. 2026.4.1.~2027.3.31. 확인서만 인정", LC_F),
    case("LC6", "PBLN127568", "2026-11-02",
         lc(main_industry_ksic="10712", industry_name="빵류 제조업", site_region="전라남도 목포시",
            other="당을 줄인 간식을 직접 만들어 완제품으로 팝니다. 혈당 관리를 하시는 분들이 많이 찾습니다. 건강기능식품 인증은 없습니다. 소상공인확인서 유효기간은 2026년 4월 1일부터 2027년 3월 31일까지입니다."),
         ASK, IN_PERIOD, ["X5"], "'관리식품'은 공고에 정의가 없어 저당 간식 해당 여부를 판단 불가", LC_F),
]

# ---------- 4. TOPS (1065812) ----------
# 자사 브랜드는 신청 요건이 아니다. 단순 유통과 25년 2단계 이상은 제외. 접수는 4.2.에 끝나 11.2. 기준은 마감이다.
TP_X1_EX = ("다단계판매 등록 영위, 부동산관리업(6821), 동일 장소 6개월 이상 중개·대리(68221)·분양 대행(68224), 공유오피스·공유주방(68112), "
            "유사의료업(86902), 시각장애인 운영 안마원·안마시술소는 신청 가능")
c_tp = [
    cond("M1", "eligibility", "small_merchant", "derived", True, "not_stated", 1, "□ (신청 자격) 소상공인"),
    cond("L1", "eligibility", "merchant_certificate", "eq", True, "not_stated", 1, "• 중소기업확인서 내 ’소상공인‘으로 기재되어 있는 기업"),
    cond("C3", "eligibility", "support_field", "in", ["식품", "홈·리빙", "패션", "뷰티"], "not_stated", 1, "* 식품 1,200개사, 홈·리빙 700개사, 패션 700개사, 뷰티 900개사"),
    cond("X1", "exclusion", "excluded_industry", "eq", False, "not_stated", 1, "소상공인 정책자금 융자제외 대상 업종은 신청 불가", exception=TP_X1_EX),
    cond("X2", "exclusion", "business_status", "not_in", ["휴업", "폐업", "부도"], "deadline_date", 1, "접수 마감일 기준 기업이 휴·폐업 또는 부도 상태인 경우"),
    cond("X3", "exclusion", "tax_arrears", "eq", False, "not_stated", 1, "국세·지방세 체납 또는 금융기관 등 채무불이행이 확인된 경우", check="declared"),
    cond("X4", "exclusion", "debt_default", "eq", False, "not_stated", 1, "국세·지방세 체납 또는 금융기관 등 채무불이행이 확인된 경우", check="declared"),
    cond("X5", "exclusion", "unfair_trade_1y", "eq", False, "not_stated", 1, "최근 1년 이내 공정거래법에 따른 불공정행위 위반 사실이 있는 경우", check="declared"),
    cond("X6", "exclusion", "product_origin", "not_in", ["해외 수입제품", "대기업 제품"], "not_stated", 1, "해외 수입제품, 대기업 제품"),
    other("X7", "exclusion", "2025년 TOPS 프로그램 2단계 이상 진출 이력 없음", 1, "‘25년 TOPS 프로그램 2단계 이상 진출 소상공인은 신청 불가"),
    cond("X8", "exclusion", "product_origin", "ne", "타사 브랜드 단순 유통·판매", "not_stated", 1, "** 타기업·소상공인의 브랜드 제품을 단순 유통·판매만 하는 경우는 지원 제외"),
    other("D1", "eligibility", "적격심사와 공동평가위원회 평가", 1, "- 수행기관별 상품기획전문가, 관련 분야 전문가가 참여하는 공동평가위원회를 통해 선정", "discretionary"),
    cond("P1", "period", "application_period", "between", ["2026-02-26", "2026-04-02T18:00"], "as_of_date", 1, "◦ (신청 기간) ’26년 2월 26일(목) ~ 4월 2일(목) 18시까지"),
]
oos_tp = [
    {"text": "컨설팅·판촉·홍보 지원, 상생성장지원자금, 소진공 사업 가점", "reason": "자격이 아니라 지원 내용"},
    {"text": "2단계 진출의 자사 브랜드 보유", "reason": "1단계 신청 요건이 아님('신청일 기준 자사 브랜드가 없어도 신청 가능'). 2단계 선발은 라벨 범위 밖"},
    {"text": "판판대로 신청, 1개 플랫폼사 선택, 제출서류, 선정 시 AI 교육 필수", "reason": "신청 절차와 선정 후 의무"},
    {"text": "재해자금 융자허용 업종 표", "reason": "재해자금 지원 범위이며 이 사업의 신청 자격 예외로 적혀 있지 않음"},
]


def tp(**k):
    p = {"main_industry_ksic": "10712", "industry_name": "빵류 제조업", "employees": 4, "revenue_3y_avg": 300000000,
         "merchant_certificate": True, "support_field": "식품", "own_brand": True, "business_status": "정상", "tax_arrears": False,
         "debt_default": False, "unfair_trade_1y": False, "product_origin": "자사 제조 제품",
         "other": "작년에 TOPS 프로그램에 참여한 적이 없습니다. 중소기업확인서에 소상공인으로 적혀 있습니다."}
    p.update(k)
    return p


TP_F = (AGENCY,)
cases_tp = [
    case("TP1", "1065812", "2026-04-02", tp(), OK, IN_PERIOD, [], "모든 값 충족, 마감일 당일은 기간 내", TP_F),
    case("TP2", "1065812", "2026-03-10",
         tp(main_industry_ksic="23221", industry_name="가정용 도자기 제조업", support_field="홈·리빙", own_brand=False,
            other="직접 만든 그릇을 팔고 아직 등록한 브랜드는 없습니다. 작년 TOPS는 1단계까지만 참여했습니다. 중소기업확인서에 소상공인으로 적혀 있습니다."),
         OK, IN_PERIOD, [], "자사 브랜드 없어도 신청 가능. 25년 1단계만 참여는 제외 아님", TP_F),
    case("TP3", "1065812", "2026-03-10",
         tp(other="작년 TOPS에서 2단계까지 진출했습니다. 중소기업확인서에 소상공인으로 적혀 있습니다."), NO, IN_PERIOD, ["X7"],
         "25년 2단계 이상 진출은 신청 불가", TP_F),
    case("TP4", "1065812", "2026-11-02",
         tp(main_industry_ksic="47813", industry_name="화장품 소매업", support_field="뷰티", own_brand=False,
            product_origin="타사 브랜드 단순 유통·판매",
            other="다른 회사 브랜드 화장품을 떼어다 그대로 팔고 있습니다. 작년에 TOPS 프로그램에 참여한 적이 없습니다. 중소기업확인서에 소상공인으로 적혀 있습니다."),
         NO, CLOSED, ["X8"], "타사 브랜드 단순 유통은 지원 제외. 기간도 마감", TP_F),
    case("TP5", "1065812", "2026-03-10",
         tp(main_industry_ksic="33999", industry_name="그 외 기타 제품 제조업", support_field="반려동물 용품",
            other="반려동물 산책 용품을 직접 만들어 팝니다. 작년에 TOPS 프로그램에 참여한 적이 없습니다. 중소기업확인서에 소상공인으로 적혀 있습니다."),
         ASK, IN_PERIOD, ["C3"], "4대 분야의 품목 정의가 공고에 없어 반려동물 용품 해당 여부 불명", TP_F),
    case("TP6", "1065812", "2026-03-20",
         {**{k: v for k, v in tp().items() if k != "debt_default"},
          "other": "작년에 TOPS 프로그램에 참여한 적이 없습니다. 중소기업확인서에 소상공인으로 적혀 있습니다. 은행 대출에 연체로 잡힌 것이 있는지 아직 확인하지 못했습니다."},
         ASK, IN_PERIOD, ["X4"], "금융기관 채무불이행 값 없음", TP_F),
]

# ---------- 5. 창업도약패키지 일반형 (1065016) ----------
# 업력은 일반·신산업·패스트트랙의 OR. 패스트트랙은 기본 요건에 고용·매출·투자 중 1개가 추가된다.
DEBT_EX = ("마감일 기준 채무변제 완료, 프리워크아웃·개인워크아웃·새출발기금 채무조정합의, 회생계획·변제계획 인가, 파산 면책 확정, "
           "재기지원보증·재창업 자금지원")
TAX_EX = "마감일 기준 강제징수·체납처분 유예, 특수채무 변제 증빙"
RECOUP_EX = "마감일까지 전액 반환, 회생·파산 면책결정, 분할납부 승인 후 정상납부"
PRIOR_EX = "글로벌기업 협업 프로그램(’19~’20년 창구, ’20년 마중, 정글, 엔업) 및 창업도약패키지 성장촉진 프로그램(’17~’21년)만 지원받은 경우 신청 가능"
CUR_EX = "공고사업과 동일연도 창업사업화 지원사업이 아닌 경우, 지자체 지원사업은 협약 잔여기간과 관계없이 신청 가능"
FT_EX = "대표자·기업명·아이템이 동일한 경우만. 중단·포기·실패 기업 제외. ’25년 참여 중이면 협약종료 전 중단·포기·실패 시 최종선정 제외"
FT, NI = "패스트트랙 기업", "신산업 창업 분야 기업"
QUAL = ("□ 신청자격 : ｢중소기업기본법｣ 제2조제1호에 따른 중소기업의 대표자이자, ｢중소기업창업 지원법｣ 동법 제2조제2호부터 제2조제3의2까지의 "
        "각 호의 정의에 따른 도약기 창업기업 또는 패스트트랙 해당기업")
c_cd = [
    other("S1", "eligibility", "중소기업기본법상 중소기업의 대표자", 1, QUAL),
    other("S2", "eligibility", "모집공고일 기준 중소기업창업 지원법상 창업기업(붙임 4 기준표)", 1, "* 단, 본 공고에 따라 창업기업의 신청자격 기준은 모집공고일 기준 창업기업으로 인정받은 경우에 한하여 참여 가능", basis="notice_date"),
    cond("F1", "eligibility", "founded_date", "between", ["2019-01-23", "2023-01-22"], "notice_date", 1, "▶ 신청가능 업력 : 2019.1.23. ~ 2023.1.22. 기간내 창업한 기업", "OR:업력"),
    cond("F2", "eligibility", "founded_date", "between", ["2016-01-23", "2023-01-22"], "notice_date", 1, "(신산업분야는 2016.1.23. ~ 2023.1.22. 기간내 창업한 기업)", "OR:업력", applies_to=NI),
    other("FT1", "eligibility", "’23~’25년 초기창업패키지, ’23~’24년 창업중심대학(초기), ’23~’25년 재도전성공패키지 참여기업", 1,
          "◦ (패스트 트랙 기업) ’23∼’25년 초기창업패키지, ’23∼’25년 재도전성공패키지, ’23~’24년 창업중심대학(초기 창업기업) 참여기업 중 [붙임 5]의 자격 요건을 충족하는 자(기업)",
          group="OR:업력", exception=FT_EX, applies_to=FT),
    cond("FT2", "eligibility", "employees", "ge", 10, "notice_date", 1, "① 공고일 기준 고용인원(대표자 제외) 10인 이상 기업", "OR:패스트트랙필수", unit="명", applies_to=FT),
    cond("FT3", "eligibility", "revenue_prev_year", "ge", 2000000000, "not_stated", 1, "② 연 매출액 20억원 이상 기업(*‘25년 결산 기준)", "OR:패스트트랙필수", unit=WON, applies_to=FT),
    other("FT4", "eligibility", "공고일 기준 누적 투자유치액 3억원 이상", 1, "③ 공고일 기준 누적 투자유치액 3억원 이상 기업", group="OR:패스트트랙필수", applies_to=FT, basis="notice_date"),
    cond("G1", "eligibility", "business_registration", "eq", True, "not_stated", 1, "* 개인‧법인사업자 모두 사업 개시 및 사업자 등록을 완료하여야 함"),
    cond("G2", "eligibility", "all_reps_eligible", "eq", True, "not_stated", 1, "• 공동대표 또는 각자대표로 구성된 기업의 경우, 대표자 전원이 ‘신청자격’에 해당되고, ‘신청 제외 대상’에 해당되지 않아야 함",
         check="declared", applies_to="공동·각자대표 기업"),
    other("G3", "eligibility", "다수 사업자등록증 보유 시 창업 여부 기준표(붙임 4)상 창업", 1, "• 다수의 사업자등록증(개인‧법인)을 보유한 경우, 창업여부 기준표에 따라 신청 자격 적합 여부 결정([붙임 4] 창업 여부 기준표를 참고하여 신청 전 필히 확인)",
          applies_to="다수 사업자 보유 기업"),
    cond("G4", "eligibility", "head_office", "eq", True, "not_stated", 1, "• 본점과 지점이 있는 경우, 본점 사업자로만 신청 가능하며 중복 신청한 경우 본점 기준으로 요건 검토 예정",
         check="declared", applies_to="본점·지점 보유 기업"),
    other("G5", "eligibility", "창업기업 확인서의 창업 기준 충족일이 모집공고일(2026-01-23) 이전(당일 포함)", 1, "창업 기준 충족일이 모집공고일 이전일 것 (모집공고일 당일 포함)", basis="notice_date"),
    cond("E1", "exclusion", "debt_default", "eq", False, "not_stated", 1, "① 금융기관 등으로부터 채무불이행으로 규제 중인 자(기업)", check="declared", exception=DEBT_EX),
    cond("E2", "exclusion", "tax_arrears", "eq", False, "not_stated", 1, "② 국세 또는 지방세 체납 중인 자(기업)", check="declared", exception=TAX_EX),
    cond("E3", "exclusion", "recoup_outstanding", "eq", False, "not_stated", 1, "③ 창업진흥원으로부터 발생한 환수금등의 반환이 종결되지 않은 자(기업)", check="declared", exception=RECOUP_EX),
    cond("E4", "exclusion", "startup_excluded_industry", "eq", False, "not_stated", 1, "④ 「중소기업창업 지원법 시행령」 제4조(창업에서 제외되는 업종)의 업종을 영위하고 있거나 영위하고자 하는 자(기업) ([붙임 1] 지원 제외 대상 업종 참조)"),
    other("E5", "exclusion", "붙임 2-1 창업사업화 지원사업 총 3회 이상 협약 이력 없음(중단 포함)", 1, "⑤ 중소벤처기업부 창업사업화 지원사업[붙임 2-1]에 총 3회 이상 선정되어 협약을 체결했던 이력이 있는 자(기업)   ※ 중단(중단처분·중도포기자) 포함"),
    cond("E6", "exclusion", "prior_restart_program", "eq", False, "not_stated", 1, "⑥ 사업연도를 불문하고, [붙임2-2]에 명시된 사업에 선정되어 협약을 체결했던 이력이 있는 자(기업)   ※ 중단(중단처분·중도포기자) 포함", check="declared", exception=PRIOR_EX),
    cond("E7", "exclusion", "current_startup_program", "eq", False, "not_stated", 1, "⑦ 2026년 중소벤처기업부 및 타 중앙정부·공공기관의 ‘창업사업화 지원사업*’에 선정되어 사업을 수행 중인 자(기업),[붙임3] 참고   ※ 중단(중단처분·중도포기자) 포함", check="declared", exception=CUR_EX),
    cond("E8", "exclusion", "gov_sanction", "eq", False, "not_stated", 1, "⑧ 중소벤처기업부 창업지원사업에 참여 제한으로 제재 중인 자", check="declared"),
    cond("E9", "exclusion", "business_status", "not_in", ["휴업", "폐업"], "application_date", 1, "⑨ 신청일 기준 동 사업에 신청하는 사업자가 휴‧폐업 중인 자(기업)"),
    cond("E10", "exclusion", "bank_account_available", "eq", True, "not_stated", 1, "⑩ 창업진흥원이 지정한 은행 계좌(사업비 계좌) 개설 및 거래가 불가한 자(기업)", check="declared"),
    cond("E11", "exclusion", "program_staff", "eq", False, "not_stated", 1, "⑪ 2026년 동 사업 주관기관의 전담조직의 장, 전담/겸직인력으로 참여 중 또는 참여 예정인 자(기업)", check="declared"),
    cond("E12", "exclusion", "wage_arrears_listed", "eq", False, "not_stated", 1, "⑫ 「근로기준법」에 따라 고용노동부가 공개하는 체불사업주 명단에 포함된 자(기업)", check="declared"),
    cond("E13", "exclusion", "subsidy_excluded", "eq", False, "not_stated", 1, "⑬ 「보조금 관리에 관한 법률」 제31조의2(보조사업 수행 배제 등)에 따라 수행대상에서 배제된 자(기업)", check="declared"),
    other("E14", "exclusion", "중소벤처기업부 장관이 인정한 참여 제한 사유", 1, "⑭ 기타 중소벤처기업부 장관이 참여를 제한할 정당한 사유가 있다고 인정하는 자(기업)", "discretionary"),
    cond("P1", "period", "application_period", "between", ["2026-01-23", "2026-02-13T16:00"], "as_of_date", 1, "□ 접수 기간 : ’26.1.23.(금) ~ 2.13.(금) 16:00까지"),
]
oos_cd = [
    {"text": "사업화 자금, 자기부담 비율, 창업프로그램, 후속지원", "reason": "자격이 아니라 지원 내용"},
    {"text": "서류·발표 평가, 가점·면제·우선선정, 단계별 60점 미만 제외", "reason": "자격이 아니라 선정 평가"},
    {"text": "본점 소재 권역 주관기관 선택, 대표자 본인 신청, 협약체결 확약서, 평가위원 참여 불가", "reason": "신청 절차와 선정 후 의무"},
    {"text": "딥테크 특화형·투자연계형", "reason": "일반형 공고가 아니라 유형별 별도 공고"},
]
TYPES_CD = [NI, FT, "공동·각자대표 기업", "다수 사업자 보유 기업", "본점·지점 보유 기업"]

CD_OTHER = ("우리 회사는 중소기업이고 제가 대표입니다. 처음 창업한 회사이고 다른 사업자는 없습니다. 창업기업 확인서의 창업 기준 충족일도 공고일 전입니다. "
            "창업사업화 지원사업 협약은 3회 미만입니다. ")


def cd(extra="", **k):
    p = {"main_industry_ksic": "62010", "industry_name": "컴퓨터 프로그래밍 서비스업", "employees": 6, "founded_date": "2021-05-10",
         "business_registration": True, "business_status": "정상", "debt_default": False, "tax_arrears": False, "recoup_outstanding": False,
         "startup_excluded_industry": False, "prior_restart_program": False, "current_startup_program": False, "gov_sanction": False,
         "bank_account_available": True, "program_staff": False, "wage_arrears_listed": False, "subsidy_excluded": False,
         "other": CD_OTHER + extra}
    p.update(k)
    return p


CD_F = (AGENCY,)
cases_cd = [
    case("CD1", "1065016", "2026-02-13",
         cd(extra="국세 체납이 있었지만 마감일 전에 강제징수 유예를 받았습니다.", founded_date="2019-01-23", tax_arrears=True, tax_arrears_exception=True),
         OK, IN_PERIOD, [], "2019-01-23은 신청가능 업력 시작일로 포함('7년 이내'). 체납은 강제징수 유예 예외. 마감일 당일은 기간 내", CD_F),
    case("CD2", "1065016", "2026-02-05",
         cd(extra="2024년 초기창업패키지에 참여해 협약을 마쳤고 대표자, 회사 이름, 아이템이 그대로입니다. 공고일에 대표자를 빼고 고용인원이 10명입니다.",
            applicant_type=FT, founded_date="2024-03-01", employees=10, revenue_prev_year=500000000),
         OK, IN_PERIOD, [], "업력은 미달이지만 패스트트랙 기본 요건 충족, 고용인원 10인 정각은 '이상'에 포함", CD_F),
    case("CD3", "1065016", "2026-02-02",
         cd(extra="패스트트랙 대상 사업에 참여한 적이 없고 신산업 분야도 아닙니다.", founded_date="2023-01-23"), NO, IN_PERIOD, ["F1"],
         "2023-01-23 창업은 공고일에 정확히 3년으로 '3년 초과' 아님", CD_F),
    case("CD4", "1065016", "2026-11-02",
         cd(extra="2022년 창업도약패키지 사업화지원에 선정돼 협약했다가 중도 포기했습니다. 다른 협업 프로그램으로 받은 것은 아닙니다.",
            prior_restart_program=True, prior_restart_program_exception=False),
         NO, CLOSED, ["E6"], "붙임 2-2 사업 협약 이력은 중도포기 포함 제외. 기간도 마감", CD_F),
    case("CD5", "1065016", "2026-02-10",
         cd(extra="지방세 체납이 있는데 유예를 받았는지 특수채무 변제가 되는지 아직 모릅니다.", tax_arrears=True),
         ASK, IN_PERIOD, ["E2"], "체납 있음, 예외 해당 여부 불명", CD_F),
    case("CD6", "1065016", "2026-11-02",
         cd(extra="AI 서비스 회사인데 신산업 창업 분야에 드는지 모르겠습니다. 패스트트랙 대상 사업에 참여한 적은 없습니다.", founded_date="2018-05-10"),
         ASK, CLOSED, ["F1", "F2"], "일반 업력은 초과, 신산업이면 가능. 신산업 고시 내용이 공고에 없고 해당 여부 불명", CD_F),
]

NOTICES = {
    "PBLN127480": ("동해시 소상공인의 카드수수료 지원 요건과 제외 대상", c_dh, oos_dh, ["공동대표 사업장", "다수 사업체 대표"]),
    "PBLN127233": ("경북 출산 소상공인의 신청 자격, 지원제외 대상, 대체인력 고용 기간 요건", c_ib, oos_ib, []),
    "PBLN127568": ("광주·전남·제주 소상공인의 현장 라이브커머스 신청 자격과 제외 품목", c_lc, oos_lc, []),
    "1065812": ("TOPS 1단계 신청 소상공인의 자격과 지원제외 대상", c_tp, oos_tp, []),
    "1065016": ("창업도약패키지 일반형의 도약기·신산업·패스트트랙 신청 자격과 신청 제외 대상", c_cd, oos_cd, TYPES_CD),
}
cases = cases_dh + cases_ib + cases_lc + cases_tp + cases_cd

CASE_NOTE = ("프로필은 전부 가상. 공고마다 일치 2, 불일치 2, 확인 필요 2. expected는 공고를 읽은 사람의 판단이며, 어휘로 못 담는 사실은 "
             "프로필 other에 글로 적고 unsupported 조건은 그 글로 판단함. '_exception' 키는 예외 해당 여부를 입력값으로 밝힌 것. "
             "as_of는 2026-11-02 또는 공고 기간 내 날짜. 1065016·1065812의 마감 사례는 2026-11-02 기준이며 자격 상태와 기간 상태를 따로 적음.")


# ---------- 인용 확인과 저장 ----------
def pages(notice_id):
    # 쪽 표시 [[pN]]로 원문을 나눈다. 인용은 줄 단위 원문 그대로여야 하므로 정규화하지 않는다.
    out, cur = {}, None
    for line in open(f"{ROOT}/text/holdout3_{notice_id}.txt", encoding="utf-8").read().split("\n"):
        if line.startswith("[[p") and line.endswith("]]"):
            cur = int(line[3:-2])
            out[cur] = []
        elif cur is not None:
            out[cur].append(line)
    return {k: "\n".join(v) for k, v in out.items()}


def check_quotes(notice_id, conditions):
    # 표시한 쪽에 문구가 있어야 한다. 하나라도 없으면 저장하지 않도록 오류 목록을 돌려준다.
    pg = pages(notice_id)
    return [(notice_id, c["id"], c["evidence"]["page"], c["evidence"]["quote"]) for c in conditions
            if c["evidence"]["quote"] not in pg.get(c["evidence"]["page"], "")]


def main():
    errors = [e for n, v in NOTICES.items() for e in check_quotes(n, v[1])]
    if errors:
        for e in errors:
            print("인용 오류", e)
        sys.exit(1)
    scope = {}
    for n, (desc, conditions, oos, types) in NOTICES.items():
        scope[n] = [desc, types]
        doc = {"source_text": f"holdout3_{n}", "scope": desc, "conditions": conditions, "out_of_scope": oos,
               "notice_id": n, "labeler": LABELER, "status": STATUS}
        json.dump(doc, open(f"{LABELS}/holdout3_{n}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(scope, open(f"{LABELS}/holdout3_scope.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"status": "AI 초안, 참가자 확인 전", "note": CASE_NOTE, "cases": cases},
              open(f"{LABELS}/holdout3_cases.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("인용 확인 통과. 조건", {n: len(v[1]) for n, v in NOTICES.items()}, "사례", len(cases))


if __name__ == "__main__":
    main()
