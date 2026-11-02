"""새 공고(holdout) 5건의 정답 라벨 작성 스크립트.

흐름: 공고별 조건 정의 → 범위 정의 → 사례 30개 정의 → 인용 문구가 표시 쪽에 있는지 확인 → JSON 저장.
목적: 시스템 출력과 독립적으로, 공고 원문만 읽고 정한 정답을 평가 전에 고정한다.
결과 해석: 파일은 AI 초안이며 참가자 확인 전이다. 인용 확인 통과는 문구 존재만 보장하고 해석의 옳음은 보장하지 않는다.

라벨 작성 원칙(이 파일의 판단 근거).
- 기준서 v7을 따른다. 어휘에 없는 요건은 field=other로 두고, 기관 재량이면 discretionary, 사실 요건이지만 구조화할 수 없으면 unsupported.
- expected는 공고를 읽은 사람의 판단이다. unsupported 요건도 프로필의 other 설명으로 사실이 확인되면 충족으로 본다.
  그래서 unsupported가 항상 적용되는 공고의 일치 사례는 판정기가 확인 필요로 낸다. 판정기 한계로 보고하고 라벨은 바꾸지 않는다.
- 공고 내 표기 충돌은 OR 그룹으로 쓴다. 엄격한 값은 profile, 느슨한 값은 conflict.
  엄격한 값 충족은 일치, 느슨한 값만 충족은 확인 필요, 둘 다 위반은 불일치가 된다.
- 프로필 보조 키: other(어휘로 못 담는 사실 설명), {field}_exception(예외 해당 여부), applicant_type,
  revenue_compare_period·revenue_before·revenue_latest, industry_name. 판정기와 기존 eval 사례가 쓰는 입력 형식이다.

해석 메모(JSON에는 note 키를 두지 않으므로 여기에 남긴다).
- 1066183 G3·M4: 모집공고일이 연장 공고 2026-03-11인지 최초 공고 2026-02-05인지 불명. 전일까지의 업력이므로 두 값을 모두 둔다.
- 1066183 E5·E6: '신청일 기준 3년'과 '’23~25년'의 범위가 다르다. 어차피 unsupported라 값으로 옮기지 않고 exception에 남긴다.
- 1069948 S1·S1b: '미만' 상한을 between에 담기 위해 499,999,999원, 0.199999로 적었다. 조건이 이중 범위라 lt로 분리하면 OR 구조가 깨진다.
- 1069948 X4: tax_arrears는 조합과 이사장 체납을 함께 묻는 값으로 쓴다.
- 1069948 X6: 참고4가 이 문서에 없지만 기준서 8장의 excluded_industry와 같은 목록 이름이라 profile로 둔다.
- 1066579 A1: 기준일이 공고일이 아닌 고정일(2026-01-22)이다. 스키마에 해당 값이 없어 notice_date로 적는다.
- PBLN127594 C8: '국세청 매출자료 미확인'은 기관이 조회해 정하는 결과라 discretionary로 둔다.
- PBLN127594 C9: 재보증 제한업종과 정책자금 지원제외 대상 두 목록의 합집합을 excluded_industry 하나로 적는다.
"""
import json
import os
import re

ROOT = os.path.expanduser("~/sosang_agent/data")
LABELS = f"{ROOT}/labels"
LABELER, STATUS = "AI 초안", "참가자 확인 전"
AGENCY = "기관 판단 표시"
CONFLICT = "근거 충돌 표시"
IN_PERIOD, CLOSED = "공고상 기간 내", "마감"
MFG = [f"C{i}" for i in range(10, 35)]


def cond(id, kind, field, op, value, basis, page, quote, group="AND", check="profile", unit=None,
         exception=None, applies_to=None, waives=None):
    # 기준서 3장의 조건 스키마 한 건을 만든다. 술어는 참이면 통과하는 방향으로 적는다.
    return {"id": id, "kind": kind, "field": field, "op": op, "value": value, "unit": unit, "basis": basis,
            "group": group, "check": check, "exception": exception, "applies_to": applies_to,
            "waives": waives or [], "evidence": {"page": page, "quote": quote}}


def other(id, kind, value, page, quote, check="unsupported", group="AND", exception=None, applies_to=None, basis="not_stated"):
    # 어휘로 담지 못하는 요건. value는 묻는 내용을 글로 적는다(기존 eval 라벨과 같은 방식).
    return cond(id, kind, "other", "eq", value, basis, page, quote, group, check, None, exception, applies_to)


# ---------- 1. 백년소상공인 신규 지정 (1066183) ----------
# 분야가 둘이므로 program으로 나눈다. 제조업 제외는 어휘의 범위 표기를 뒤집어 not_in으로 적는다.
BN_QUOTE_EX = "◦(계속영업) 주된업종의변동없이계속사업을유지하여야함"
BN_SANCTION = "· 신청일 기준 3년(‘23~25년) 이내 산업재해 명단공표, 임금체불, 불공정행위,"
BN_RANGE_NOTE = "'신청일 기준 3년'과 '’23~25년'의 범위가 달라 2026년 처분·2023년 초 처분의 포함 여부 불명"
BN_MERGE = "재창업·상속·증여·승계 시 업력 합산 가능, 인정 여부는 선정평가위원회가 최종 판정. 휴·폐업 기간은 제외"
c_1066183 = [
    cond("G1", "eligibility", "small_merchant", "derived", True, "not_stated", 1, "(백년가게) 업력30년이상의소상공인(제조업제외)", applies_to="백년가게"),
    cond("G2", "eligibility", "main_industry_ksic", "not_in", MFG, "not_stated", 2, "(백년가게) 제조업을제외한업력30년이상의소상공인", unit="KSIC 중분류", applies_to="백년가게"),
    cond("G3a", "eligibility", "founded_date", "le", "1996-02-04", "notice_date", 2, "등기일을기준으로모집공고일전일까지의영업기간", "OR:백년가게업력", exception=BN_MERGE, applies_to="백년가게"),
    cond("G3b", "eligibility", "founded_date", "le", "1996-03-10", "notice_date", 1, "2026년3월11일", "OR:백년가게업력", "conflict", applies_to="백년가게"),
    cond("M1", "eligibility", "small_craft_business", "derived", True, "not_stated", 1, "(백년소공인) 업력15년이상의숙련기술기반의소공인(제조업)", applies_to="백년소공인"),
    cond("M2", "eligibility", "main_industry_ksic", "between", ["C10", "C34"], "not_stated", 2, "(백년소공인) 상시근로자10인미만의제조업을주된사업*으로영", unit="KSIC 중분류", applies_to="백년소공인"),
    cond("M3", "eligibility", "employees", "lt", 10, "not_stated", 2, "(백년소공인) 상시근로자10인미만의제조업을주된사업*으로영", unit="명", applies_to="백년소공인"),
    cond("M4a", "eligibility", "founded_date", "le", "2011-02-04", "notice_date", 2, "등기일을기준으로모집공고일전일까지의영업기간", "OR:백년소공인업력", exception=BN_MERGE, applies_to="백년소공인"),
    cond("M4b", "eligibility", "founded_date", "le", "2011-03-10", "notice_date", 1, "2026년3월11일", "OR:백년소공인업력", "conflict", applies_to="백년소공인"),
    other("M5", "eligibility", "숙련기술 기반 해당 여부", 1, "(백년소공인) 업력15년이상의숙련기술기반의소공인(제조업)", "discretionary", applies_to="백년소공인"),
    other("C1", "eligibility", "주된 업종 변동 없이 계속 영업(불가피한 일시 중단 제외)", 2, BN_QUOTE_EX),
    cond("C2", "eligibility", "joint_rep_main", "eq", True, "not_stated", 1, "* 공동대표의 경우 주 대표자가 신청", check="declared", exception="공동대표가 아니면 통과"),
    other("C3", "eligibility", "백년가게·백년소공인 중복 신청 아님", 4, "□백년가게와백년소공인간중복신청불가"),
    other("C4", "eligibility", "업력 합산 등 인정 여부", 4, "□업력합산등인정여부는선정평가위원회에서최종판정", "discretionary"),
    cond("E1", "exclusion", "excluded_industry", "eq", False, "application_date", 4, "· 소상공인정책자금 지원제외 업종을 영위하고 있는 경우(참고2)"),
    cond("E2", "exclusion", "business_status", "not_in", ["휴업", "폐업", "부도"], "application_date", 4, "· 신청일 기준 기업의 부도, 휴·폐업 중인 경우"),
    cond("E3", "exclusion", "tax_arrears", "eq", False, "application_date", 4, "· 국세·지방세 체납, 금융기관 등의 채무불이행이 확인된 경우", check="declared"),
    cond("E4", "exclusion", "debt_default", "eq", False, "application_date", 4, "· 국세·지방세 체납, 금융기관 등의 채무불이행이 확인된 경우", check="declared"),
    other("E5", "exclusion", "3년 이내 과징금·영업정지·품목제조정지·형사처벌 등 행정처분 이력 없음", 4, "· 신청일 기준 3년(‘23~25년) 이내 과징금, 영업정지, 품목제조정지, 형사처벌", exception=BN_RANGE_NOTE, basis="application_date"),
    other("E6a", "exclusion", "3년 이내 산업재해 명단공표 이력 없음", 4, BN_SANCTION, exception=BN_RANGE_NOTE, basis="application_date"),
    other("E6b", "exclusion", "3년 이내 임금체불 이력 없음", 4, BN_SANCTION, exception=BN_RANGE_NOTE, basis="application_date"),
    other("E6c", "exclusion", "3년 이내 불공정행위 이력 없음", 4, BN_SANCTION, exception=BN_RANGE_NOTE, basis="application_date"),
    other("E6d", "exclusion", "3년 이내 고액 상습체납 이력 없음", 4, "고액 상습체납 이력이 있는 경우", exception=BN_RANGE_NOTE, basis="application_date"),
    other("E7", "exclusion", "프랜차이즈 가맹점·대리점 아님", 4, "· 프랜차이즈 가맹점 및 대리점", exception="프랜차이즈 본사는 신청 가능", basis="application_date"),
    cond("P1", "period", "application_period", "between", ["2026-02-05", "2026-03-27T18:00"], "as_of_date", 1, "다. 모집기간: 2026. 2. 5.(목) ~ 2026. 3. 27.(금), 18:00까지"),
]
oos_1066183 = [
    {"text": "마이데이터 동의, 대표자 직접 회원가입", "reason": "자격이 아니라 신청 절차"},
    {"text": "서류·현장평가 지표와 가점", "reason": "자격이 아니라 선정 평가"},
]

# ---------- 2. 협업활성화 공동사업 2차 (1069948) ----------
# 신청 주체는 applicant_type(협동조합·자율상권조합), 성장단계는 program으로 나눈다.
# OR 안의 AND를 표현할 수 없어 단계별 단서는 exception에 원문으로 남긴다.
c_1069948 = [
    cond("T1", "eligibility", "support_field", "eq", "공동장비", "not_stated", 1, "‘공동일반’ 유형 신청은 1차 공고 시 마감되었으며, 본 공고는 ‘공동장비’ 유형에 한정하여 신청이"),
    cond("T2", "eligibility", "business_registration", "eq", True, "application_date", 5, "* 신청일 기준 법인 설립이 완료된 조합 및 연합회에 한함"),
    other("A1", "eligibility", "전체 조합원 5인 이상", 5, "설립된 전체 조합원이", applies_to="협동조합(연합회)"),
    other("A2", "eligibility", "조합원(회원) 50% 이상이 소상공인", 5, "5인 이상이고, 조합원(회원) 50% 이상이 소상공인*으로 구성된 협동", applies_to="협동조합(연합회)"),
    other("A3", "eligibility", "협동조합기본법·중소기업협동조합법에 따라 설립, 수익사업 영위", 5, "1) 협동조합기본법 : 영리 또는 수익사업을 하는 협동조합(연합회)", applies_to="협동조합(연합회)"),
    other("A4", "eligibility", "지역상권법에 근거해 설립, 수익사업 영위", 5, "3) 지역상권 상생 및 활성화에 관한 법률 : 수익사업을 영위하는 자율상권조합", applies_to="자율상권조합"),
    cond("S1", "eligibility", "revenue_prev_year", "between", [10000000, 499999999], "not_stated", 6, "①‘25년 매출액 1천만원 이상~5억원 미만", "OR:성장단계", unit="원",
         exception="’25년 매출액이 없어도 ‘25년~’26년 설립 조합은 성장단계 신청 가능", applies_to="성장단계"),
    cond("S1b", "eligibility", "revenue_change_rate", "between", [0.05, 0.199999], "not_stated", 6, "②’24년대비‘25년매출액증가율5% 이상~20% 미만", "OR:성장단계", unit="비율", applies_to="성장단계"),
    cond("D1", "eligibility", "revenue_prev_year", "ge", 500000000, "not_stated", 6, "① ‘25년 매출액 5억원 이상", "OR:도약단계", unit="원", applies_to="도약단계"),
    cond("D2", "eligibility", "revenue_change_rate", "ge", 0.2, "not_stated", 6, "② ’24년 대비 ‘25년 매출액 증가율 20% 이상", "OR:도약단계", unit="비율",
         exception="단, ②의 경우 ’24년 매출액 1천만원 이상", applies_to="도약단계"),
    cond("I1", "eligibility", "revenue_prev_year", "ge", 1000000000, "not_stated", 6, "① ‘25년 매출액 10억원 이상", "OR:혁신성장단계", unit="원", applies_to="혁신성장단계"),
    other("I2", "eligibility", "조합원 출자금 1억원 이상(등기부등본 기준), 단 ’25년 매출액 1천만원 이상", 6, "② 조합원 출자금 규모 1억원 이상(등기부등본 기준)", group="OR:혁신성장단계", applies_to="혁신성장단계"),
    other("X1", "exclusion", "’20~’25년 협업활성화 공동사업 5회 지원 이력 없음", 10, "①‘20년부터 ’25년까지 소상공인 협업활성화 공동사업을 5회 지원받은 조합(연합회)"),
    cond("X2", "exclusion", "subsidy_excluded", "eq", False, "not_stated", 10, "② 보조금 관리에 관한 법률, 국가를 당사자로 하는 계약에 관한 법률, 국고보조금", check="declared"),
    cond("X3", "exclusion", "gov_sanction", "eq", False, "not_stated", 10, "③ 중소벤처기업부 및 소상공인시장진흥공단 사업에 참여제한으로 제재 중인 경우", check="declared"),
    cond("X4", "exclusion", "tax_arrears", "eq", False, "not_stated", 10, "④ 협동조합(연합회) 및 조합 이사장(연합회장)의 국세 및 지방세 체납사실이 있는 경우", check="declared"),
    cond("X5a", "exclusion", "business_status", "not_in", ["휴업", "폐업"], "not_stated", 10, "⑤ 휴‧폐업중인 협동조합(연합회) 또는 조합원(회원)의 50% 이상이 휴‧폐업중인 협동조합(연합회)"),
    other("X5b", "exclusion", "조합원(회원) 50% 이상 휴·폐업 아님", 10, "⑤ 휴‧폐업중인 협동조합(연합회) 또는 조합원(회원)의 50% 이상이 휴‧폐업중인 협동조합(연합회)"),
    cond("X6", "exclusion", "excluded_industry", "eq", False, "not_stated", 10, "⑥ 소상공인정책자금 지원제외 업종*(“참고4”)을 영위하고 있는 협동조합(연합회) 및", applies_to="협동조합(연합회)"),
    cond("X6b", "exclusion", "excluded_industry", "eq", False, "not_stated", 10, "** 자율상권조합의 경우, 조합 및 조합원이 임대업을 영위하는 경우에도 신청 가능",
         exception="자율상권조합은 임대업을 영위해도 신청 가능", applies_to="자율상권조합"),
    other("X6c", "exclusion", "조합원(회원)의 주된 사업이 지원제외 업종 아님", 10, "* 주된 사업(연매출액 비중이 가장 큰 사업) 기준"),
    other("X7", "exclusion", "대기업·대기업 프랜차이즈 가맹점 아님", 10, "⑦ 대기업 및 대기업 프랜차이즈 가맹점"),
    other("X8", "exclusion", "장관·이사장이 인정하는 참여 제한 사유 해당 여부", 10, "⑧ 기타 중소벤처기업부 장관 또는 소상공인시장진흥공단 이사장이 참여를 제한할", "discretionary"),
    cond("X9", "exclusion", "prior_similar_benefit", "eq", False, "not_stated", 1, "활성화 판로지원사업(’26. 3. 24 공고)에 선정된 경우 신청 불가", check="declared"),
    cond("P1", "period", "application_period", "between", ["2026-07-21", "2026-08-04T16:00"], "as_of_date", 1, "’26. 7. 21.(화) ~ ‘26. 8. 4.(화), 16:00까지"),
]
oos_1069948 = [
    {"text": "공동일반 유형", "reason": "1차 공고로 마감, 본 공고는 공동장비만 신청 가능"},
    {"text": "품목별 장비 요건(구매단가 3백만원 이상, 신청 불가 장비, 설치 장소)", "reason": "조합 자격이 아니라 지원 대상 장비 요건"},
    {"text": "선정 우대와 가점", "reason": "자격이 아니라 선정 평가"},
]

# ---------- 3. 예비창업패키지 수정 2차 (1066579) ----------
# 분야는 program(일반·여성·소셜벤처), 폐업 이력·부동산임대업 대표는 applicant_type으로 나눈다.
c_1066579 = [
    cond("A1", "eligibility", "business_registration", "eq", False, "notice_date", 2, "◦신청자명의의사업자등록증을보유하고있지않으며, 법인의법률상", "OR:사업자등록"),
    cond("A1b", "eligibility", "founded_date", "ge", "2026-01-23", "not_stated", 2, "※ ’26.1.23. 이후 사업자등록 또는 법인등기를 완료한 경우 신청 가능", "OR:사업자등록", waives=["A1"]),
    cond("A1c", "eligibility", "rental_only_no_staff_individual", "eq", True, "notice_date", 2, "▖’26.1.22. 기준, 직원을 고용하지 않고, 부동산임대업만을 영위하는 개인사업자", "OR:사업자등록", "declared", waives=["A1"]),
    cond("A2", "eligibility", "can_restart_by_deadline", "eq", True, "not_stated", 2, "▖다만, 협약 종료일 2개월 이전까지 이종업종의 제품·서비스를 영위하는 법인사업자로 창업", check="declared", applies_to="부동산임대업 대표"),
    other("A3", "eligibility", "법인의 법률상 대표권 없음(’26.1.23. 이후 등기 완료 제외)", 2, "※ 법인등기부상 대표이사, 각자대표, 공동대표, 대표권 있는 사내이사인 경우 신청 불가", basis="notice_date"),
    cond("C1a", "exclusion", "closure_date", "lt", "2026-01-28", "notice_date", 2, "②사업공고일기준최근1개월(’26.1.28.~2.27.) 내개인사업자폐업또는", "OR:폐업시점", applies_to="폐업 이력자"),
    cond("C1b", "exclusion", "closure_date", "le", "2026-01-28", "notice_date", 2, "- 다만, ‘26.1.28.(수) 이전의", "OR:폐업시점", "conflict", applies_to="폐업 이력자"),
    other("C2", "eligibility", "이종업종 창업 예정, 또는 동종업종이면 폐업 후 3년(부도·파산 2년) 경과", 2, "❷동종업종창업예정인경우,", applies_to="폐업 이력자"),
    other("T1", "eligibility", "기술창업을 영위하려는 자", 1, "※ 「중소기업창업 지원법」 제2조제4호·제9호에 따른 기술창업을 영위하고자 하는 자"),
    other("F1", "eligibility", "여성 예비창업자", 2, "혁신적인 기술창업 아이디어를 보유한 여성 예비창업자에 한함", applies_to="여성"),
    other("F2", "eligibility", "사회문제 해결 목표의 소셜벤처 창업 여부", 2, "사회문제 해결을 목표로 혁신기술 또는 비즈니스 모델을 통해 수익을", "discretionary", applies_to="소셜벤처"),
    cond("E1", "exclusion", "debt_default", "eq", False, "deadline_date", 2, "① 금융기관 등으로부터 채무불이행으로 규제 중인 자", check="declared",
         exception="채무변제 완료, 채무조정 합의, 회생·변제계획 인가, 면책 확정, 재기지원보증·재창업 자금지원(마감일 기준)"),
    cond("E2", "exclusion", "tax_arrears", "eq", False, "deadline_date", 2, "② 국세 또는 지방세 체납 중인 자", check="declared",
         exception="강제징수·체납처분 유예, 특수채무 변제 증빙(마감일 기준)"),
    cond("E3", "exclusion", "recoup_outstanding", "eq", False, "deadline_date", 2, "③ 창업진흥원으로부터 발생한 환수금 등의 반환이 종결되지 않은 자", check="declared",
         exception="전액 반환, 면책 결정, 분할납부 정상 이행(마감일 기준)"),
    cond("E4", "exclusion", "startup_excluded_industry", "eq", False, "not_stated", 3, "④ 「중소기업창업 지원법 시행령」 제4조에 따른 창업 제외 업종을 영위하고자 하는 자"),
    cond("E5", "exclusion", "prior_restart_program", "eq", False, "not_stated", 3, "⑤ 사업연도를 불문하고, [붙임2]에 명시된 사업에 선정되어 협약을 체결한 이력이 있는 자", check="declared",
         exception="’19년 이후 예비창업패키지 수혜자로 ‘최우수’ 평가를 받고 공고일 기준 만 39세 이하면 제외"),
    cond("E6", "exclusion", "current_startup_program", "eq", False, "not_stated", 3, "⑥ 2026년 중앙정부·공공기관 창업사업화 지원사업 수행 중인 자(기업), [붙임3] 참고", check="declared",
         exception="같은 연도 창업사업화 지원사업이 아닌 경우 신청 가능"),
    cond("E7", "exclusion", "gov_sanction", "eq", False, "not_stated", 3, "⑦ 창업지원사업 참여제한 제재 중인 자", check="declared"),
    cond("E8", "exclusion", "bank_account_available", "eq", True, "not_stated", 3, "⑧ 창업진흥원이 지정한 은행 계좌(사업비 계좌) 개설 및 거래가 불가한 자", check="declared"),
    cond("E9", "exclusion", "program_staff", "eq", False, "not_stated", 3, "⑨ 2026년 동 사업 주관기관의 전담조직의 장, 전담/겸직인력으로 참여 중 또는 참여 예", check="declared"),
    cond("E10", "exclusion", "wage_arrears_listed", "eq", False, "not_stated", 3, "⑩ 「근로기준법」에 따른 고용노동부 체불사업주 명단 공개 대상자", check="declared"),
    cond("E11", "exclusion", "subsidy_excluded", "eq", False, "not_stated", 3, "⑪ 「보조금 관리에 관한 법률」 제31조의2에 따른 수행배제 대상자", check="declared"),
    other("E12", "exclusion", "장관 인정 제한 사유 해당 여부", 3, "⑫ 기타 중소벤처기업부 장관이 참여 제한할 사유가 있다고 인정하는 자", "discretionary"),
    other("E13", "exclusion", "친족 합산 의결권 주식 50% 초과 과점 주주 아님", 3, "⑬ 친족과 합하여 의결권 있는 주식 50% 초과 보유한 과점 주주"),
    cond("P1", "period", "application_period", "between", ["2026-03-06", "2026-03-26T18:00"], "as_of_date", 3, "□ 접수 기간 : ’26. 3. 6.(금) ~ 3. 26.(목), 18:00까지"),
]
oos_1066579 = [
    {"text": "사내벤처 분야", "reason": "별도 공고 예정"},
    {"text": "서류평가 가점·면제·우선 선정", "reason": "자격이 아니라 선정 평가"},
    {"text": "신청자의 동 사업 평가위원 참여 불가", "reason": "신청 자격 표 밖의 유의사항"},
]

# ---------- 4. 정읍시 카드수수료 미신청자 (PBLN127594) ----------
# HWPX라 쪽이 1개다. 1인 2개 사업체 한도는 해당자에게만 적용되도록 유형으로 분리한다.
JE_REV_EX = "'국세청 홈택스 카드매출액 기준'이 3억 판정 기준인지 지원금 산정 기준인지 불명"
c_PBLN127594 = [
    cond("C1", "eligibility", "small_merchant", "derived", True, "not_stated", 1, "전년도(2025년) 매출액 3억 원 이하 소상공인 중"),
    cond("C2", "eligibility", "revenue_prev_year", "le", 300000000, "not_stated", 1, "전년도(2025년) 매출액 3억 원 이하 소상공인 중", unit="원", exception=JE_REV_EX),
    cond("C3", "eligibility", "applied_earlier_round", "eq", False, "not_stated", 1, "2026년도 7월(1차신청) 미신청 업채", check="declared"),
    cond("C4", "exclusion", "prior_similar_benefit", "eq", False, "not_stated", 1, "※ 2026년 정읍시 소상공인 카드수수료 지원사업 1차 기지급업체 제외", check="declared"),
    cond("C5", "eligibility", "site_region", "eq", "정읍시", "notice_date", 1, "○ 전년도(2025년) 및 당해 연도(2026년) 정읍시 내에서 사업 영위하는 소상공인"),
    cond("C6", "exclusion", "business_status", "not_in", ["폐업"], "notice_date", 1, "(공고일 기준 폐업, 타 시도 이전 등으로 요건을 만족하지 못할 시 지원대상에서 제외)"),
    cond("C7", "exclusion", "founded_date", "le", "2025-12-31", "not_stated", 1, "※ 2026년 신규 개업자, 국세청 매출자료 미확인자 지급제외"),
    other("C8", "exclusion", "국세청 매출자료 확인 여부", 1, "※ 2026년 신규 개업자, 국세청 매출자료 미확인자 지급제외", "discretionary"),
    cond("C9", "exclusion", "excluded_industry", "eq", False, "not_stated", 1, "○ 제외업종 : 도박 및 성인용품 판매점 등"),
    other("J1", "eligibility", "1인당 2개 사업체 이내", 1, "○ 1인이 다수 사업체 소유 시 1인당 2개 사업체까지 인정", applies_to="다수 사업체 소유자"),
    cond("P1", "period", "application_period", "between", ["2026-11-02", "2026-11-20"], "as_of_date", 1, "□ 접수기간 : 2026. 11. 2.(월) ~ 11. 20.(금)"),
]
oos_PBLN127594 = [
    {"text": "지원금 산정(카드 매출액 0.4%, 최대 30만원)", "reason": "자격이 아니라 지원 내용"},
    {"text": "대리인 신청 서류, 읍·면·동 방문 신청", "reason": "자격이 아니라 신청 절차"},
]

# ---------- 5. 경북 소담스타 (PBLN127590) ----------
# 원문은 글자가 흩어진 추출본이다. 인용은 공백을 뺀 대조로 확인되는 조각을 쓰고, 값은 흩어진 숫자를 맞춰 읽었다.
SD_ONLINE = "이상 또는 온라인 매출액 천만원 이상"
SD_OTHER = "프랜차이즈 가맹점ㆍ직영점대기업 및 그 출자업체유관기관정부 및 공공기관"
c_PBLN127590 = [
    cond("A1", "eligibility", "small_merchant", "derived", True, "notice_date", 2, "공고일 기준 소상공인기본법 제조의 소상공인으로 경상북도에"),
    cond("A2", "eligibility", "hq_region", "eq", "경상북도", "notice_date", 1, "요건을 충족하는 경상북도 소재 소상공인본점 기준"),
    other("A3", "eligibility", "디지털커머스 성과 창출 사례 보유 여부", 2, "디지털커머스 성과 창출 사례 보유 기업전략스토리 등", "discretionary"),
    cond("B1", "eligibility", "revenue_prev_year", "ge", 100000000, "not_stated", 2, "년 매출액 억 원 이상", unit="원"),
    other("B2a", "eligibility", "온라인 매출 비중 30% 이상", 2, SD_ONLINE, group="OR:온라인매출"),
    other("B2b", "eligibility", "온라인 매출액 5천만원 이상", 2, SD_ONLINE, group="OR:온라인매출"),
    cond("G1", "eligibility", "revenue_change_rate", "gt", 0, "not_stated", 2, "전년 대비 매출액 증가", unit="비율"),
    other("G2", "eligibility", "전년도 영업이익 흑자", 2, "전년도 영업이익 흑자"),
    other("L1", "eligibility", "지역자원 활용도", 2, "지역자원 활용도지역에 존재하는 유무형의 인적물적 자원", "discretionary"),
    other("L2", "eligibility", "지역경제·지역사회에 미치는 영향력", 2, "지역경제지역사회에 미치는 영향력", "discretionary"),
    cond("E1", "exclusion", "business_status", "not_in", ["휴업", "폐업", "부도"], "deadline_date", 6, "신청마감일 기준 기업의 부도휴ㆍ폐업 중인 경우"),
    cond("E2", "exclusion", "tax_arrears", "eq", False, "not_stated", 6, "국세지방세 체납금융기관 등의 채무불이행이 확인된 경우", check="declared"),
    cond("E3", "exclusion", "debt_default", "eq", False, "not_stated", 6, "국세지방세 체납금융기관 등의 채무불이행이 확인된 경우", check="declared"),
    other("E4", "exclusion", "프랜차이즈 가맹점·직영점 아님", 6, SD_OTHER),
    other("E5", "exclusion", "대기업 및 그 출자업체 아님", 6, SD_OTHER),
    other("E6", "exclusion", "유관기관(정부 및 공공기관) 아님", 6, SD_OTHER),
    cond("E7", "exclusion", "excluded_industry", "eq", False, "not_stated", 6, "소상공인 정책자금 융자 제외 업종유흥ㆍ사행성 등을 영위하는 경우"),
    cond("P1", "period", "application_period", "between", ["2026-10-27", "2026-11-03T18:00"], "as_of_date", 1, "공고일로부터 년 월 일화 까지 2026 11 03 ( ) 18:00"),
]
oos_PBLN127590 = [
    {"text": "우대사항(매출 3억원 이상·상근근로자 1명 이상, 영업이익 30% 증가)", "reason": "자격이 아니라 가점"},
    {"text": "활동기간 종료일까지 경북 내 사업자등록 유지", "reason": "선정 후 의무"},
    {"text": "제출 서류(중소기업확인서, 4대보험 명부 등)", "reason": "자격이 아니라 제출 절차"},
]

NOTICES = {
    "1066183": ("백년가게·백년소공인 신청 자격과 지원 제외", c_1066183, oos_1066183, ["백년가게", "백년소공인"]),
    "1069948": ("공동장비 유형 신청 자격과 신청 제외. 신청 주체(협동조합·자율상권조합)와 성장단계별 요건 포함", c_1069948, oos_1069948,
                ["협동조합(연합회)", "자율상권조합", "성장단계", "도약단계", "혁신성장단계"]),
    "1066579": ("일반·여성·소셜벤처 분야 신청 자격, 자격 예외, 신청 제외", c_1066579, oos_1066579,
                ["일반", "여성", "소셜벤처", "폐업 이력자", "부동산임대업 대표"]),
    "PBLN127594": ("미신청 소상공인 지원대상과 지급·업종 제외", c_PBLN127594, oos_PBLN127594, ["다수 사업체 소유자"]),
    "PBLN127590": ("경북 소재 소상공인 신청 요건과 지원 제외", c_PBLN127590, oos_PBLN127590, []),
}


# ---------- 사례 ----------
def case(id, notice_id, program, as_of, profile, expected, period, decisive, reason, flags=(AGENCY,)):
    # 다섯 공고 모두 항상 적용되는 재량 조항이 있어 기관 판단 표시가 기본값이다.
    return {"id": id, "notice_id": notice_id, "program": program, "as_of": as_of, "profile": profile,
            "expected": expected, "period_status": period, "decisive": decisive, "reason": reason, "flags": list(flags)}


# 백년소상공인: 공고일 표기 충돌, 제조업 제외, 10인 경계, 승계 업력이 어려운 지점이다.
BN_CLEAN = ("최근 3년 행정처분·산업재해 명단공표·임금체불·불공정행위·고액 상습체납 이력 없음. 프랜차이즈 가맹점·대리점 아님. "
            "주된 업종 변동과 영업 중단 없음. 백년가게·백년소공인 중복 신청 아님.")


def bn(**k):
    p = {"tax_arrears": False, "debt_default": False, "business_status": "정상", "joint_rep_main": True, "other": BN_CLEAN}
    p.update(k)
    return p


FOOD_MFG = dict(main_industry_ksic="10712", industry_name="떡류 제조업", revenue_3y_avg=300000000)
RESTAURANT = dict(main_industry_ksic="56111", industry_name="한식 일반 음식점업", employees=3, revenue_3y_avg=500000000)
cases = [
    case("BN1", "1066183", "백년가게", "2026-03-20", bn(founded_date="1990-04-01", **RESTAURANT), "일치", IN_PERIOD, [],
         "개업 36년, 음식점 3명. 기준일은 옛 마감 3.10 뒤지만 연장된 기간 안"),
    case("BN2", "1066183", "백년소공인", "2026-03-27", bn(founded_date="2011-02-04", employees=9, **FOOD_MFG), "일치", IN_PERIOD, [],
         "제조업 9명은 10인 미만, 2.4 기준으로도 업력 15년 정각. 마감 당일"),
    case("BN3", "1066183", "백년가게", "2026-03-20", bn(founded_date="1985-06-01", employees=3, **FOOD_MFG), "불일치", IN_PERIOD, ["G2"],
         "떡류 제조업은 제조업이라 백년가게 분야 제외"),
    case("BN4", "1066183", "백년소공인", "2026-03-20", bn(founded_date="2000-06-01", employees=10, **FOOD_MFG), "불일치", IN_PERIOD, ["M3"],
         "상시근로자 10명은 10인 미만 아님"),
    case("BN5", "1066183", "백년가게", "2026-11-02", bn(founded_date="1996-02-20", **RESTAURANT), "확인 필요", CLOSED, ["G3a", "G3b"],
         "최초 공고 2.5 기준 30년 미만, 연장 공고 3.11 기준 30년 이상. 모집공고일 표기로 갈림. 기간은 마감", (AGENCY, CONFLICT)),
    case("BN6", "1066183", "백년소공인", "2026-03-20",
         bn(founded_date="2018-05-01", employees=4, other=BN_CLEAN + " 부친이 1995년 개업한 공방을 상속받아 2018년 재개업, 기술 전수 확약서 준비 중.", **FOOD_MFG),
         "확인 필요", IN_PERIOD, ["M4a"], "자기 업력은 15년 미만. 승계 합산 인정 여부는 평가위원회 판정이라 예외 해당 여부 불명"),
]

# 협업활성화: 1차 탈락 재신청, 임대업 예외, 증가율 단서, 이사장 체납이 어려운 지점이다.
CO_CLEAN = ("조합원 12명, 그중 소상공인 8명. 협동조합기본법에 따라 설립, 수익사업 영위. 공동사업 지원 이력 2회. "
            "조합원 휴·폐업 없음. 조합원 주된 사업이 제외 업종 아님. 대기업·대기업 프랜차이즈 가맹점 아님.")


def co(**k):
    p = {"applicant_type": "협동조합(연합회)", "support_field": "공동장비", "business_registration": True, "subsidy_excluded": False,
         "gov_sanction": False, "tax_arrears": False, "business_status": "정상", "prior_similar_benefit": False,
         "main_industry_ksic": "10799", "industry_name": "그 외 기타 식품 제조업", "other": CO_CLEAN}
    p.update(k)
    return p


cases += [
    case("CO1", "1069948", "성장단계", "2026-07-28",
         co(revenue_prev_year=499000000, applied_earlier_round=True, other=CO_CLEAN + " 1차 공고에 신청했으나 미선정."),
         "일치", IN_PERIOD, [], "’25 매출 4.99억은 5억 미만. 1차 미선정은 '선정된 경우' 제외 아님"),
    case("CO2", "1069948", "도약단계", "2026-07-28",
         co(applicant_type="자율상권조합", revenue_prev_year=600000000, main_industry_ksic="68112", industry_name="비주거용 건물 임대업",
            other="지역상권법에 근거해 설립한 자율상권조합, 임대 수익사업 영위. 공동사업 지원 이력 1회. 조합원 휴·폐업 없음. 조합원 주된 사업은 임대업 외 제외 업종 아님. 대기업·대기업 프랜차이즈 가맹점 아님."),
         "일치", IN_PERIOD, [], "매출 6억, 자율상권조합은 임대업 영위 시에도 신청 가능"),
    case("CO3", "1069948", "도약단계", "2026-07-28",
         co(revenue_prev_year=9600000, revenue_compare_period="2024년→2025년", revenue_before=8000000, revenue_latest=9600000),
         "불일치", IN_PERIOD, ["D1", "D2"], "증가율 20%지만 ’24 매출 800만원으로 '1천만원 이상' 단서 미충족, 매출도 5억 미만"),
    case("CO4", "1069948", "성장단계", "2026-07-28",
         co(revenue_prev_year=200000000, tax_arrears=True, other=CO_CLEAN + " 조합 체납은 없으나 이사장 지방세 체납 있음."),
         "불일치", IN_PERIOD, ["X4"], "제외 사유는 조합과 이사장 모두의 체납을 포함"),
    case("CO5", "1069948", "혁신성장단계", "2026-11-02", co(revenue_prev_year=800000000), "확인 필요", CLOSED, ["I2"],
         "매출 8억은 10억 미만. 다른 경로인 출자금 규모 미입력. 기간은 마감"),
    case("CO6", "1069948", "성장단계", "2026-07-28",
         co(revenue_prev_year=200000000, other=CO_CLEAN.replace("조합원 주된 사업이 제외 업종 아님.", "조합원 1명이 부동산 임대업과 음식점을 겸업, 매출 비중 미확인.")),
         "확인 필요", IN_PERIOD, ["X6c"], "주된 사업 기준인데 매출 비중을 몰라 조합원의 제외 업종 해당 여부 불명"),
]

# 예비창업패키지: 1.22·1.23 기준일, 1.28 폐업 경계, 중도포기 포함, 채무 예외가 어려운 지점이다.
YC_CLEAN = "소프트웨어 기술창업 준비. 법인 대표권 없음. 과점 주주 아님."


def yc(**k):
    p = {"business_registration": False, "debt_default": False, "tax_arrears": False, "recoup_outstanding": False,
         "startup_excluded_industry": False, "prior_restart_program": False, "current_startup_program": False, "gov_sanction": False,
         "bank_account_available": True, "program_staff": False, "wage_arrears_listed": False, "subsidy_excluded": False, "other": YC_CLEAN}
    p.update(k)
    return p


cases += [
    case("YC1", "1066579", "일반", "2026-03-20",
         yc(applicant_type="폐업 이력자", closure_date="2026-01-27", other=YC_CLEAN + " 이전 사업은 한식 음식점(56111), 창업 예정은 58222로 이종업종."),
         "일치", IN_PERIOD, [], "1.27 폐업은 1.28 이전, 세세분류가 달라 이종업종"),
    case("YC2", "1066579", "여성", "2026-03-26",
         yc(business_registration=True, founded_date="2026-02-10", other=YC_CLEAN + " 여성 신청자."),
         "일치", IN_PERIOD, [], "1.23 이후 사업자등록은 신청 가능. 마감 당일"),
    case("YC3", "1066579", "일반", "2026-03-20", yc(business_registration=True, founded_date="2026-01-22", rental_only_no_staff_individual=False),
         "불일치", IN_PERIOD, ["A1", "A1b", "A1c"], "기준일 1.22 당일 등록이라 1.23 이후 예외 아님"),
    case("YC4", "1066579", "일반", "2026-03-20",
         yc(prior_restart_program=True, prior_restart_program_exception=False, other=YC_CLEAN + " 2024년 청년창업사관학교 협약 후 중도 포기."),
         "불일치", IN_PERIOD, ["E5"], "붙임2 사업 협약 이력은 중도포기 포함, 최우수 예외 아님"),
    case("YC5", "1066579", "소셜벤처", "2026-03-20",
         yc(applicant_type="폐업 이력자", closure_date="2026-01-28", other=YC_CLEAN + " 이전 사업은 한식 음식점(56111), 창업 예정은 58222로 이종업종."),
         "확인 필요", IN_PERIOD, ["C1b"], "1.28은 '1개월 내(1.28~2.27) 불가'와 '1.28 이전 가능'에 모두 해당", (AGENCY, CONFLICT)),
    case("YC6", "1066579", "일반", "2026-11-02", yc(debt_default=True, other=YC_CLEAN + " 개인회생 신청 진행 중, 변제계획 인가 여부 모름."),
         "확인 필요", CLOSED, ["E1"], "채무불이행 있음, 인가 예외 해당 여부 불명. 기간은 마감"),
]


# 정읍: 3억 이하 경계, 2025-12-31 개업, 1차 신청 후 미지급, 총매출과 카드매출, 재보증 제한업종이 어려운 지점이다.
def je(**k):
    p = {"site_region": "전북특별자치도 정읍시", "business_status": "정상", "applied_earlier_round": False, "prior_similar_benefit": False,
         "founded_date": "2018-03-02", "main_industry_ksic": "56111", "industry_name": "한식 일반 음식점업", "employees": 2,
         "revenue_prev_year": 200000000, "revenue_3y_avg": 200000000}
    p.update(k)
    return p


cases += [
    case("JE1", "PBLN127594", None, "2026-11-02", je(revenue_prev_year=300000000, revenue_3y_avg=300000000), "일치", IN_PERIOD, [],
         "매출 3억 정각은 '이하'. 접수 첫날"),
    case("JE2", "PBLN127594", None, "2026-11-20",
         je(founded_date="2025-12-31", main_industry_ksic="47411", industry_name="남자용 겉옷 소매업", employees=4, revenue_prev_year=20000000, revenue_3y_avg=20000000),
         "일치", IN_PERIOD, [], "2025-12-31 개업은 2026년 신규 개업 아님. 접수 마지막 날"),
    case("JE3", "PBLN127594", None, "2026-11-02",
         je(revenue_prev_year=300000001, revenue_3y_avg=300000001, revenue_prev_year_exception=False, other="2025년 카드 매출액도 300,000,001원."),
         "불일치", IN_PERIOD, ["C2"], "총매출과 카드매출 모두 3억 초과라 어느 기준이든 위반"),
    case("JE4", "PBLN127594", None, "2026-11-02", je(applied_earlier_round=True, other="7월 1차에 신청했으나 서류 미비로 지급받지 못함."),
         "불일치", IN_PERIOD, ["C3"], "기지급 여부와 별개로 대상은 1차 미신청 업체"),
    case("JE5", "PBLN127594", None, "2026-11-02",
         je(revenue_prev_year=340000000, revenue_3y_avg=340000000, other="2025년 카드 매출액 2억 6천만원."),
         "확인 필요", IN_PERIOD, ["C2"], "총매출은 3억 초과, 카드매출은 이하. '카드매출액 기준'의 적용 대상이 불명"),
    case("JE6", "PBLN127594", None, "2026-11-02",
         je(main_industry_ksic="46331", industry_name="주류 도매업", employees=4),
         "확인 필요", IN_PERIOD, ["C9"], "붙임의 보증 제한업종. 면허 보유 시 제외한다는 단서가 있는데 면허 미입력"),
]

# 소담스타: 1억 경계, 온라인 OR, 증가 0원, 본점 기준, 일부 제외 코드가 어려운 지점이다.
SD_CLEAN = "2025년 영업이익 흑자 1,800만원. 프랜차이즈 가맹점·직영점 아님. 대기업·출자업체 아님. 유관기관·공공기관 아님."


def sd(online="온라인 매출 비중 40%, 온라인 매출액 8천만원.", **k):
    p = {"hq_region": "경상북도 구미시", "main_industry_ksic": "10799", "industry_name": "그 외 기타 식품 제조업", "employees": 3,
         "revenue_3y_avg": 200000000, "revenue_prev_year": 200000000, "revenue_compare_period": "2024년→2025년",
         "revenue_before": 180000000, "revenue_latest": 200000000, "business_status": "정상", "tax_arrears": False, "debt_default": False,
         "other": f"{online} {SD_CLEAN}"}
    p.update(k)
    return p


cases += [
    case("SD1", "PBLN127590", None, "2026-11-02", sd(online="온라인 매출 비중 25%, 온라인 매출액 5천만원."), "일치", IN_PERIOD, [],
         "비중은 30% 미만이지만 온라인 매출액 5천만원 이상으로 OR 충족"),
    case("SD2", "PBLN127590", None, "2026-11-03",
         sd(online="온라인 매출 비중 30%, 온라인 매출액 3천만원.", revenue_prev_year=100000000, revenue_3y_avg=100000000, revenue_before=90000000, revenue_latest=100000000),
         "일치", IN_PERIOD, [], "매출 1억 정각과 온라인 비중 30% 정각은 모두 '이상'. 마감 당일"),
    case("SD3", "PBLN127590", None, "2026-11-02", sd(hq_region="서울특별시 성동구", site_region="경상북도 구미시"), "불일치", IN_PERIOD, ["A2"],
         "공장은 경북이지만 본점 기준 요건은 서울로 위반"),
    case("SD4", "PBLN127590", None, "2026-11-02", sd(revenue_before=200000000, revenue_latest=200000000), "불일치", IN_PERIOD, ["G1"],
         "전년과 매출이 같아 '증가' 아님"),
    case("SD5", "PBLN127590", None, "2026-11-02",
         sd(founded_date="2025-03-10", revenue_prev_year=150000000, revenue_3y_avg=150000000, revenue_compare_period=None, revenue_before=None, revenue_latest=None),
         "확인 필요", IN_PERIOD, ["G1"], "2025년 3월 개업이라 전년 대비 매출 증가를 판단할 비교값이 없음"),
    case("SD6", "PBLN127590", None, "2026-11-02", sd(main_industry_ksic="47859", industry_name="그 외 기타 분류 안된 상품 전문 소매업"), "확인 필요", IN_PERIOD, ["E7"],
         "47859는 코드 중 성인용품 판매점만 제외. 세부 업종 미입력"),
]

CASE_NOTE = ("프로필은 전부 가상. 공고마다 일치 2, 불일치 2, 확인 필요 2로 구성해 조정 없음. "
             "expected는 공고를 읽은 사람의 판단이며, 어휘로 못 담는 사실은 프로필 other에 글로 적고 unsupported 조건은 그 글로 판단함. "
             "'_exception' 키는 예외 미해당을 입력값으로 밝힌 것. as_of는 2026-11-02 또는 공고 기간 내 날짜.")


# ---------- 인용 확인과 저장 ----------
def norm(s):
    # 추출 텍스트의 줄바꿈과 공백 차이는 인용 오류로 보지 않는다(validate_gold와 같은 기준).
    return re.sub(r"\s+", "", s)


def pages(notice_id):
    parts = re.split(r"\[\[p(\d+)\]\]", open(f"{ROOT}/text/holdout_{notice_id}.txt").read())
    return {int(parts[i]): norm(parts[i + 1]) for i in range(1, len(parts), 2)}


def check_quotes(notice_id, conditions):
    # 표시한 쪽에 문구가 있어야 한다. 하나라도 없으면 저장하지 않도록 오류 목록을 돌려준다.
    pg = pages(notice_id)
    return [(notice_id, c["id"], c["evidence"]["page"], c["evidence"]["quote"]) for c in conditions
            if norm(c["evidence"]["quote"]) not in pg.get(c["evidence"]["page"], "")]


def clean_profile(p):
    # 값이 없는 키는 입력하지 않은 것과 같으므로 파일에 남기지 않는다.
    return {k: v for k, v in p.items() if v is not None}


def main():
    errors = [e for n, v in NOTICES.items() for e in check_quotes(n, v[1])]
    if errors:
        for e in errors:
            print("인용 오류", e)
        raise SystemExit(1)
    scope = {}
    for n, (desc, conditions, oos, types) in NOTICES.items():
        scope[n] = [desc, types]
        doc = {"source_text": f"holdout_{n}", "scope": desc, "conditions": conditions, "out_of_scope": oos,
               "notice_id": n, "labeler": LABELER, "status": STATUS}
        json.dump(doc, open(f"{LABELS}/holdout_{n}.json", "w"), ensure_ascii=False, indent=1)
    json.dump(scope, open(f"{LABELS}/holdout_scope.json", "w"), ensure_ascii=False, indent=1)
    for c in cases:
        c["profile"] = clean_profile(c["profile"])
    json.dump({"status": "AI 초안, 참가자 확인 전", "note": CASE_NOTE, "cases": cases},
              open(f"{LABELS}/holdout_cases.json", "w"), ensure_ascii=False, indent=1)
    print("조건", {n: len(v[1]) for n, v in NOTICES.items()}, "사례", len(cases))


if __name__ == "__main__":
    main()
