"""새 공고(holdout4)의 정답 라벨 작성 스크립트.

흐름: 공고별 조건 정의 → 범위 정의 → 사례 정의 → 인용 문구가 표시 쪽에 있는지 확인 → JSON 저장.
목적: 시스템 출력과 독립적으로, 공고 원문만 읽고 정한 정답을 평가 전에 고정한다.
결과 해석: 파일은 AI 초안이며 참가자 확인 전이다. 인용 확인 통과는 문구 존재만 보장하고 해석의 옳음은 보장하지 않는다.
  판정기 점검(src/check_holdout4_20261102_v1.py)의 불일치는 라벨을 맞추는 신호가 아니라 보고 대상이다.

라벨 작성 원칙.
- 기준서 v7을 따른다. 어휘에 없는 요건은 field=other로 두고, 기관 재량이면 discretionary, 사실 요건이지만 구조화할 수 없으면 unsupported.
- expected는 공고를 읽은 사람의 판단이다. unsupported 요건도 프로필 other 문장으로 사실이 확인되면 충족·위반을 판단한다.
- 인용은 쪽 원문의 한 줄 안에서 글자 그대로 잡는다. 저장 전에 원문 부분 문자열인지 코드로 확인한다.
- 프로필 보조 키: other, {field}_exception, applicant_type, industry_name.
- 조기 마감 표시는 기간이 끝나지 않은 사례에만 붙인다. 마감 뒤에는 조기 마감 가능성이 의미가 없다.

제외 공고.
- PBLN127456(청주 시제품 바우처): 원문 파일에 쪽 표시 [[p1]]만 있고 본문이 없다. 지원 대상·제외 조건이 없어 라벨을 만들지 않고 scope에서 뺀다.

해석 메모(JSON에는 조건별 note 키를 두지 않으므로 여기에 남긴다).
- 1068837 P1: 종료가 '예산 소진 시'뿐이고 날짜가 없어 4장 '종료일이 공고에 없으면 일정 확인 필요'를 적용하고 조기 마감을 표시한다.
  회차표(1차 6.8 13시~6.19 17시 등)는 회차 사이 공백이 있으나 전체 기간의 종료일이 아니므로 exception에만 적는다.
- 1068837 X11: 표는 '2개 이상 업종이면 매출액 비중이 가장 큰 업종이 주업종'이라고 적는다. 참가자 원칙 '적힌 업종에 부수적으로 해당해도 불일치'와 부딪힌다.
  어느 쪽이 우선인지 정하지 않고, 겸업 사례를 만들지 않는다. 참가자 확인 항목이다.
- 1068837 X11: '46331, 3'은 표 항목명(주류, 담배 도매업)에 따라 46331·46333으로 읽었다.
- 1068837 X5: '’26.2.1일 기준'은 고정 날짜라 basis 어휘에 맞는 값이 없어 not_stated로 두고 exception에 적는다.
  협약이 그 전날 끝났으면 해당하지 않는 것으로 읽었다(LG1).
- 1068837 X6a: 표의 '70% 미만'만 참여제한이다. 70~85% 미만의 감점은 선정 평가라 out_of_scope다. '‘24.2.1일 이후'는 당일 포함(LG3).
- 1068837 X10: '인정되는 경우'라 기관 재량으로 둔다.
- 1066053 P1: '사업공고 게시일부터 예산소진시까지'와 '신청기간 3.9~3.30'이 함께 있다. 신청 항목의 날짜를 쓰고, 조기 종료와 공고 문구는 exception에 적는다.
- 1066053 C2: 1인기업은 본문 제외 목록에 없고 별첨 적격평가 표의 예시 체크(미해당)에만 나온다. 제외 요건인지 원문으로 정할 수 없어 unsupported로 두고 TP5의 확인 필요 사유로 쓴다.
- 1066053 X4b: '기타 정상인 금융거래가 어려운 경우 등'은 기준이 없어 unsupported다. 연체가 여기에 드는지 판단할 수 없어 TP6은 확인 필요다.
- 1066053 D1: 본문은 '60점 미만 지원불가', 별첨은 '60점 이하 지원불가'다. 점수는 평가 결과라 사장님이 알 수 없어 discretionary로 두고 표기 차이는 exception에 적는다.
- 1066053 X1: 공고의 예시는 '유흥·향락업, 숙박·음식업, 불건전 오락용품 제조업 등 영위기업 등'이다. 예외가 아니라 exception에 적지 않는다. 음식업을 겸하면 참가자 원칙대로 부수적이어도 불일치로 둔다(TP3). 이 공고에는 주업종 기준 문구가 없다.
- 1066477 A3a·A3b: 신청대상은 '비수도권'인데 별첨5 지방기업 우대 분류표에 인천 강화·웅진(원문 표기, 11쪽은 옹진), 경기 가평·연천이 올라 있다.
  참가자 원칙 '표기가 갈리는 소재지는 넓게 적힌 쪽을 인정'을 적용해 OR로 두고 IV2를 일치로 정한다. 별첨5는 보조비율 표이므로 자격 근거로 볼 수 없다는 반대 해석이 가능하다. 참가자 확인 항목이다.
- 1066477 A3a exception: 지역 이전 예정 기업은 선정 후 7일 내 이전 조건으로 신청이 열려 있다. '이전 예정'의 기준이 없어 시기 미정이면 확인 필요다(IV5).
- 1066477 A5: 별첨2는 업종군별 한도라 조건 하나의 값으로 옮기기 어려워 글로 적는다. 표의 병합칸은 추출 순서대로 1~2번 140억, 3~15번 120억, 16~24번 80억, 25번 15억으로 읽었다.
  이 표는 제조 소기업에만 적용한다. 스타트업의 소기업 여부는 A1로 묻는다. 공고에 스타트업의 업력 정의는 없다.
- 1066477 X12·X13: 신청 전 유의사항의 '차년도 신청 불가'를 2025년 사업 이력에 대한 제외로 읽었다. 협약 포기는 단정 문구라 unsupported, 서비스 계약 미완료는 '처리될 수 있음'이라 discretionary다.
- 1069787 A1·A2: 규모 확대로 소상공인이 아니게 되면 사유 발생 다음 연도부터 3년간 소상공인으로 보므로 OR로 둔다. 2024년 사유면 2025~2027년(BN2), 2022년 사유면 2023~2025년(BN4).
- 1069787 A3: 참고1의 만료일은 월까지만 있고 9월 10건, 10월 6건, 11월 355건이며 12월은 0건이다. 본문 구간은 12.31까지라 12월 만료 업체는 명단과 어긋난다. 지정서 날짜와 명단이 어긋나면 확인 필요다(BN5). 사례는 업체명을 쓰지 않는다.
- 1069787 X1·X2: 원문이 '제외될 수 있음'이지만 자격요건 서류검토의 사실 항목이라 재량으로 보지 않고 사실 조건으로 둔다. 참가자 확인 항목이다.
"""
import json
import os
import sys

ROOT = os.path.expanduser("~/sosang_agent/data")
LABELS = f"{ROOT}/labels"
LABELER, STATUS = "AI 초안", "참가자 확인 전"
AGENCY = "기관 판단 표시"
EARLY = "조기 마감 가능 표시"
IN_PERIOD, CLOSED, UNKNOWN = "공고상 기간 내", "마감", "일정 확인 필요"
OK, NO, ASK = "일치", "불일치", "확인 필요"


def cond(id, kind, field, op, value, basis, page, quote, group="AND", check="profile", unit=None,
         exception=None, applies_to=None):
    # 기준서 3장의 조건 스키마 한 건. 술어는 참이면 통과하는 방향으로 적는다.
    return {"id": id, "kind": kind, "field": field, "op": op, "value": value, "unit": unit, "basis": basis,
            "group": group, "check": check, "exception": exception, "applies_to": applies_to,
            "waives": [], "evidence": {"page": page, "quote": quote}}


def other(id, kind, value, page, quote, check="unsupported", group="AND", exception=None, applies_to=None, basis="not_stated"):
    # 어휘로 담지 못하는 요건. value는 묻는 내용을 글로 적는다.
    return cond(id, kind, "other", "eq", value, basis, page, quote, group, check, None, exception, applies_to)


# ---------- 1. 일반 물류바우처 2차 (1068837) ----------
# 지원대상은 중소기업 한 줄이고 나머지는 신청 제외 목록이다. 3~4쪽에 걸쳐 있다.
LG_DEBT_EX = ("신용회복위원회 프리워크아웃·개인워크아웃 채무조정합의서 체결, 개인회생 변제계획인가, 파산면책 선고, 회생인가 등 "
              "정부·공공기관으로부터 재기지원 필요성을 인정받은 기업은 참여 가능")
LG_PRIOR_EX = ("’26.2.1 기준. 지사화사업, OK FTA, 인증취득, 박람회 등 특정 수출서비스 개별사업은 중복신청 가능(동일 유사 항목 중복정산 금지)")
LG_IND_EX = ("표의 中 표기는 일부 업종만 제외: 33402 中 불건전 영상게임기, 33409 中 도박게임장비 등, 46102 中 담배 중개, "
             "46~47 中 도박기계·사행성·불건전 오락기구, 사행성·사치성 상품 중개·도소매, 주류·담배 소매, 58 中 불건전 게임소프트웨어, "
             "76390 中 도박기계 등 임대. 전체 제외: 46331·46333 주류·담배 도매, 5621 주점업, 9124 사행시설 관리·운영. "
             "2개 이상 업종이면 매출액 비중이 가장 큰 업종이 주업종")
c_1068837 = [
    other("C1", "eligibility", "중소기업기본법 제2조 및 시행령 제3조에 따른 중소기업", 3, "제2조및시행령제3조에따른중소기업"),
    cond("X1", "exclusion", "business_status", "not_in", ["휴업", "폐업"], "not_stated", 3, "◈ 휴·폐업했거나 국세·지방세 체납중인 경우"),
    cond("X2", "exclusion", "tax_arrears", "eq", False, "not_stated", 3, "◈ 휴·폐업했거나 국세·지방세 체납중인 경우", check="declared"),
    cond("X3", "exclusion", "debt_default", "eq", False, "not_stated", 3, "◈ 민사집행법에 의하여 채무불이행자명부에 등재되거나, 전국은행연합회 등",
         check="declared", exception=LG_DEBT_EX),
    cond("X4", "exclusion", "gov_sanction", "eq", False, "not_stated", 3, "◈ 보조금법 위반 등 부정행위로 인해 정부 지원 사업에 참여제한 중인 기업", check="declared"),
    cond("X5", "exclusion", "prior_similar_benefit", "eq", False, "not_stated", 3, "◈ 산업부 수출바우처에 참여기업으로 선정되어 협약이 종료되지 않는 기업",
         check="declared", exception=LG_PRIOR_EX),
    other("X6a", "exclusion", "’24.2.1 이후 수출바우처사업 선정기업으로 바우처 사용률 70% 미만이어서 협약시작일부터 2년간 참여제한 중이 아님", 3,
          "◈ 최근 2년 중기부 수출바우처사업 참여 이력이 있는 기업 중 바우처 협약액"),
    other("X7a", "exclusion", "수출바우처 사업 수행기관으로 참여 중이 아님", 4, "◈ 수출바우처 사업 수행기관으로 참여 중이거나 부정행위 등으로 사업 참여"),
    other("X7b", "exclusion", "수행기관의 부정행위 등으로 사업 참여 제한 중이 아님", 4, "◈ 수출바우처 사업 수행기관으로 참여 중이거나 부정행위 등으로 사업 참여"),
    other("X8", "exclusion", "’26년 참여기업과 특수관계가 아님(대표자 동일, 대표자 가족 운영 등. 판단기준은 관리지침)", 4, "◈ ’26년 참여기업과 특수관계에 있는 기업"),
    cond("X9", "exclusion", "multiple_business_applying", "eq", False, "not_stated", 4, "◈ 동일 법인의 복수 사업자는 협약기간 내 동시 신청 및 선정 불가",
         check="declared", applies_to="동일 법인 복수 사업자"),
    cond("X10", "exclusion", "social_issue", "eq", False, "not_stated", 4, "◈ 사회적 물의를 일으켜 지원이 적합하지 않다고 인정되는 경우", check="discretionary"),
    cond("X11", "exclusion", "excluded_industry", "eq", False, "not_stated", 4, "◈ 사행산업 등 국민 정서상 지원이 부적절한 업종 영위 기업", exception=LG_IND_EX),
    cond("P1", "period", "application_period", "between", ["2026-06-08", None], "as_of_date", 1, "□신청기간및신청방법: 공고일~ 예산소진시까지회차별접수",
         exception="예산 소진 시 조기 마감. 2주 단위 회차별 접수(1차 6.8 13시~6.19 17시, 2차 6.22 13시~7.3 17시 등). 일정은 변경될 수 있음"),
]
oos_1068837 = [
    {"text": "모집규모, 기업당 15백만원 한도, 정부지원 70%·자부담 30%", "reason": "자격이 아니라 지원 내용"},
    {"text": "인코텀즈 C·D 조건, 정산 가능·불가 항목, 합산 100만원 이상", "reason": "신청 자격이 아니라 물류비 정산 기준"},
    {"text": "공인인증서, 필수 서류, 본인 신청, 타인 작성 금지", "reason": "자격이 아니라 신청 절차"},
    {"text": "바우처 사용률 70% 이상 85% 미만의 5점 감점", "reason": "자격이 아니라 선정 평가"},
    {"text": "사실상 동일기업 의심 시 현장조사", "reason": "제외 사유가 아니라 확인 절차"},
]

# ---------- 2. 기술보호 바우처 (1066053) ----------
# 제외 목록은 1쪽, 신청기간과 적격평가는 2쪽, 1인기업 항목은 6쪽 별첨에 있다.
c_1066053 = [
    other("C1", "eligibility", "중소기업기본법 제2조 및 시행령 제3조에 따른 중소기업", 1, "◦「중소기업기본법」제2조및시행령제3조에따른중소기업"),
    other("C2", "exclusion", "1인기업이 아님(별첨 적격평가 표의 기본검토 항목. 본문 제외 목록에는 없음)", 6, "1인기업 여부"),
    cond("X1", "exclusion", "startup_excluded_industry", "eq", False, "not_stated", 1, "1. 「중소기업창업 지원법」 제5조 및 동법 시행령 제4조의 “창업에서 제외되는 업종”에 "),
    cond("X2", "exclusion", "tax_arrears", "eq", False, "not_stated", 1, "2. 국세 및 지방세 체납 또는 휴·폐업중인 기업", check="declared"),
    cond("X3", "exclusion", "business_status", "not_in", ["휴업", "폐업"], "not_stated", 1, "2. 국세 및 지방세 체납 또는 휴·폐업중인 기업"),
    cond("X4a", "exclusion", "misuse_history", "eq", False, "not_stated", 1, "3. 신청기업의 허위 서류제출 또는 기타 정상인 금융거래가 어려운 경우 등", check="declared"),
    other("X4b", "exclusion", "정상적인 금융거래가 어려운 경우가 아님", 1, "3. 신청기업의 허위 서류제출 또는 기타 정상인 금융거래가 어려운 경우 등"),
    other("X5", "exclusion", "종전 기술보호 바우처 지원사업 참여 후 중도포기한 이력이 없음", 1, "4. 종전 기술보호 바우처 지원사업에 참여하여, 중도포기한 기업",
          exception="기존 사업 참여기업의 재신청은 가능"),
    other("D1", "eligibility", "적격평가 점수 60점 이상(2인 평균)", 2, "◦(적격평가) 점수60점미만(2인평균)은지원불가", "discretionary"),
    cond("P1", "period", "application_period", "between", ["2026-03-09", "2026-03-30"], "as_of_date", 2, "◦(신청기간) ‘26. 3. 9(월) ~ 3. 30(월)",
         exception="신청 현황에 따라 조기 종료될 수 있음. 사업공고는 게시일부터 예산소진시까지로 적힘"),
]
oos_1066053 = [
    {"text": "수준진단 점수별 바우처 한도, 정부보조율, 7년 이내 창업기업 상향", "reason": "자격이 아니라 지원 내용"},
    {"text": "참여신청서, 추진계획서, 사업자등록증 등 제출 서류", "reason": "자격이 아니라 신청 절차"},
    {"text": "2026년 사업 협약 후 포기 시 2년간 지원 불가, 계열사·협력사 서비스 이용 불가, 부정행위 제재", "reason": "선정 후 의무와 제재"},
    {"text": "연계사업 우대가점과 증빙", "reason": "자격이 아니라 연계사업 가점"},
]

# ---------- 3. 혁신바우처 지역제조 (1066477) ----------
# 컨소시엄 구성기업이 각각 신청한다. 사례는 구성기업 한 곳의 사장이 입력하고 applicant_type으로 역할을 밝힌다.
IV_DEBT_EX = "회생인가를 받은 기업, 중진공 등으로부터 재창업자금을 지원받은 기업 등 정부·공공기관으로부터 재기지원 필요성을 인정받은 기업(인)은 참여 가능"
IV_MOVE_EX = "지역 이전 예정 기업은 선정 이후 7일 이내 사업장 이전 불이행 시 선정 취소"
METRO = ["서울특별시", "인천광역시", "경기도"]
c_1066477 = [
    other("A1", "eligibility", "중소기업기본법 제2조에 따른 소기업", 4, "- 「중소기업기본법｣제2조에따른소기업",
          exception="스타트업은 예비 창업자도 신청 가능(단, 선정 시 사업자등록 필수)"),
    other("A2", "eligibility", "스타트업 1개사와 제조 소기업 1개사로 시제품 제작 컨소시엄을 구성", 4, "- 시제품제작을위한컨소시엄*을구성한기업"),
    cond("A3a", "eligibility", "site_region", "not_in", METRO, "not_stated", 2, "□신청대상: 비수도권동일(인접) 시‧도내에위치한스타트업과제조", "OR:비수도권", exception=IV_MOVE_EX),
    cond("A3b", "eligibility", "site_region", "in", ["인천광역시 강화군", "인천광역시 옹진군", "경기도 가평군", "경기도 연천군"], "not_stated", 13, "강화군, 웅진군", "OR:비수도권"),
    other("A4", "eligibility", "컨소시엄 구성기업이 모두 동일 시·도 또는 경계를 접한 시·도에 위치", 4, "- 컨소시엄구성기업이모두비수도권동일(또는인접*) 시·도에위치하는기업",
          exception="제주도는 비수도권 전체와 협업 가능"),
    other("A5", "eligibility", "별첨2 주된 업종별 평균매출액등 이하(C19·C24 140억원, C10·C11·C14·C15·C20·C21·C23·C25·C26·C28·C29·C30·C32 120억원, "
          "C12·C13·C16·C17·C18·C22·C27·C31·C33 80억원, C34 15억원)", 8, "제조 소기업 규모 기준*", applies_to="제조 소기업"),
    cond("A6", "eligibility", "main_industry_ksic", "between", ["C10", "C34"], "not_stated", 8, "* 중소기업기본법 시행령 제8조①항 별표3 분류기호 “C”", applies_to="제조 소기업"),
    cond("X1", "exclusion", "debt_default", "eq", False, "not_stated", 2, "◈ 금융기관으로부터 불량거래처로 규제중인 기업", check="declared", exception=IV_DEBT_EX),
    cond("X2", "exclusion", "tax_arrears", "eq", False, "not_stated", 2, "◈ 국세 및 지방세 체납 기업 또는 대표자", check="declared"),
    cond("X3", "exclusion", "business_status", "not_in", ["휴업", "폐업"], "not_stated", 2, "◈ 휴·폐업 기업"),
    cond("X4", "exclusion", "excluded_industry", "eq", False, "not_stated", 2, "◈ 불건전 영상게임기 제조업, 도박게임장비 등 불건전 오락용품 제조업"),
    other("X5a", "exclusion", "중소기업 혁신바우처 사업 운영기관으로 참여하는 기업이 아님", 2, "◈ 중소기업 혁신바우처 사업 운영기관으로 참여하고 있는 기업 또는 그 특수관계 기업"),
    other("X5b", "exclusion", "혁신바우처 운영기관의 특수관계 기업이 아님", 2, "◈ 중소기업 혁신바우처 사업 운영기관으로 참여하고 있는 기업 또는 그 특수관계 기업"),
    other("X6", "exclusion", "컨소시엄이 특수관계 기업으로 구성되지 않음", 2, "◈ 특수관계 기업으로 컨소시엄이 구성된 경우"),
    cond("X7", "exclusion", "prior_similar_benefit", "eq", False, "not_stated", 2, "◈ 신청 프로그램의 내용이 동 사업 및 타부처 정부지원 사업을 통해 지원받은 내용과", check="declared"),
    cond("X8", "exclusion", "selected_earlier_round", "eq", False, "application_date", 2, "◈ 신청일 현재 ‘26년 동사업에 선정된 기업", check="declared"),
    other("X9", "exclusion", "혁신바우처 사업 총 지원 횟수 5회 미만", 2, "◈ 혁신바우처 사업을 총 5회 이상 지원받은 기업"),
    cond("X10", "exclusion", "gov_sanction", "eq", False, "not_stated", 2, "◈ 대표자 또는 기업이 보조금법 위반 등으로 정부 지원사업에 참여제한 중인 경우", check="declared"),
    cond("X11", "exclusion", "social_issue", "eq", False, "not_stated", 2, "◈ 대표자 또는 기업이 그 밖에 사회적 물의를 일으켜 지원이 합당하지 않다고 인정", check="discretionary"),
    other("X12", "exclusion", "전년도 사업 선정 후 바우처 협약을 포기한 이력이 없음", 3, "◈ 선정 후 바우처 협약* 포기 시 차년도 사업 신청 불가"),
    other("X13", "exclusion", "전년도 사업 선정 후 서비스 계약 미완료로 차년도 신청 불가 처리되지 않음", 3, "취소 및 차년도 신청 불가 처리될 수 있음", "discretionary"),
    cond("P1", "period", "application_period", "between", ["2026-03-20T10:00", "2026-04-03T18:00"], "as_of_date", 2, "□신청기간: ‘26. 3. 20.(금) 10시~ ‘26. 4. 3.(금) 18시"),
]
oos_1066477 = [
    {"text": "컨소시엄당 1억원, 프로그램별 한도, 매출액별 정부지원 비율, 지역별 추가 비율", "reason": "자격이 아니라 지원 내용"},
    {"text": "구성기업 각각 신청, 공동인증서, 협업계획서와 증명 서류", "reason": "자격이 아니라 신청 절차"},
    {"text": "서면심사, 발표평가, 사업운영위원회", "reason": "자격이 아니라 선정 평가"},
    {"text": "별첨3 평균매출액 산정 방법", "reason": "별도 조건이 아니라 A5 입력값의 계산 방법"},
    {"text": "선정 후 30일 내 협약, 50일 내 서비스 계약, 7일 내 사업장 이전 이행", "reason": "선정 후 의무"},
]

# ---------- 4. 백년소상공인 재지정 (1069787) ----------
# 신규 지정이 아니라 만료 예정 업체의 재지정이다. 요건은 1쪽에 있고, 참고1은 업체 명단이다.
c_1069787 = [
    cond("A1", "eligibility", "small_merchant", "derived", True, "application_date", 1, "다. 대상규모 : ‘26년9 ~ 12월지정만료백년소상공인371개사중신청일", "OR:소상공인"),
    other("A2", "eligibility", "규모 확대 등으로 소상공인에 해당하지 않게 된 사유 발생 연도의 다음 연도부터 3년 이내", 1,
          "따라 규모의 확대 등으로 소상공인에 해당하지 아니하게 된 경우에는 그 사유가 ", group="OR:소상공인",
          exception="소기업 외의 기업과 합병하거나 그 밖에 대통령령으로 정하는 사유로 소상공인에 해당하지 않게 된 경우는 제외"),
    other("A3", "eligibility", "2026.9.1~12.31 중 지정기간 만료 예정 백년소상공인(참고1 명단 대상)", 1, "※ 본 공고는 2026. 9. 1 ~ 12. 31 중 지정기간 만료예정인 백년소상공인을 대상으로"),
    cond("X1", "exclusion", "business_status", "not_in", ["휴업", "폐업", "부도"], "application_date", 1, "* 신청일 기준 휴·폐업, 부도, 세금 체납 등이 확인될 경우 평가대상에서 제외될 수 있음"),
    cond("X2", "exclusion", "tax_arrears", "eq", False, "application_date", 1, "* 신청일 기준 휴·폐업, 부도, 세금 체납 등이 확인될 경우 평가대상에서 제외될 수 있음", check="declared"),
    other("D1", "exclusion", "행정처분 이력의 감점 또는 탈락 반영", 2, "◦행정처분이력이확인되는경우평가에서감점또는탈락사유로반영", "discretionary"),
    other("D2", "eligibility", "심의위원회의 서류·현장평가 종합심사와 최종 재지정 여부", 1, "◦(심의위원회) 전문가로구성된심의위원회에서서류및현장평가", "discretionary"),
    cond("P1", "period", "application_period", "between", ["2026-07-14", "2026-07-29T18:00"], "as_of_date", 1, "나. 신청기간: ‘26. 7. 14(화) ~ 7. 29(수), 18:00 까지"),
]
oos_1069787 = [
    {"text": "소·중기업으로 성장한 업체의 명예 백년소상공인 지정", "reason": "재지정 요건이 아니라 별도 지정. '지정될 수 있습니다'로 기준 없음"},
    {"text": "지정기간 5년, 홍보·연계 지원", "reason": "자격이 아니라 지원 내용"},
    {"text": "가점 항목과 인정 기준", "reason": "자격이 아니라 선정 평가"},
    {"text": "역량기술서, 소상공인24 신청, 승계 서류, 마이데이터 미동의 추가 서류, 보완 기한", "reason": "자격이 아니라 신청 절차·제출 서류"},
]

NOTICES = {
    "1068837": ("일반 물류바우처(2차) 참여기업의 지원대상과 신청 제외", c_1068837, oos_1068837, ["동일 법인 복수 사업자"]),
    "1066053": ("기술보호 바우처 참여기업의 지원요건과 신청 제외", c_1066053, oos_1066053, []),
    "1066477": ("혁신바우처(지역제조) 컨소시엄 구성기업의 신청 대상과 신청 제외", c_1066477, oos_1066477, ["스타트업", "제조 소기업"]),
    "1069787": ("2026년 9~12월 지정 만료 예정 백년소상공인의 재지정 신청 요건", c_1069787, oos_1069787, []),
}


# ---------- 사례 ----------
def case(id, notice, as_of, profile, expected, period, decisive, reason, flags):
    return {"id": id, "notice_id": notice, "program": None, "as_of": as_of, "profile": profile, "expected": expected,
            "period_status": period, "decisive": decisive, "reason": reason, "flags": flags}


LG_OK = ("중소기업확인서가 있는 중소기업입니다. 저나 가족이 운영하는 다른 회사는 없고 사업자도 이곳 하나입니다. "
         "수출바우처 수행기관으로 참여한 적이 없고 참여 제한을 받은 적도 없습니다.")


def lg(note="중기부 수출바우처에 참여한 적이 없습니다. 산업부 수출바우처에도 선정된 적이 없습니다.", **kw):
    # 물류바우처 기본 프로필: 모든 제외 사유에 해당하지 않는 화장품 제조 중소기업. 사례는 필요한 값만 바꾼다.
    p = {"main_industry_ksic": "20423", "industry_name": "화장품 제조업", "employees": 12, "business_status": "정상",
         "tax_arrears": False, "debt_default": False, "gov_sanction": False, "prior_similar_benefit": False,
         "excluded_industry": False, "multiple_business_applying": False, "social_issue": False, "other": f"{LG_OK} {note}"}
    p.update(kw)
    return p


LG_F = [AGENCY, EARLY]
cases = [
    case("LG1", "1068837", "2026-11-02",
         lg("수출 실적은 아직 없습니다. 중기부 수출바우처에 참여한 적이 없습니다. 산업부 수출바우처 협약은 2026년 1월 31일에 끝났습니다."),
         OK, UNKNOWN, [], "산업부 협약이 기준일 ’26.2.1 전날 종료. 수출액·매출액 기준은 미적용이라 수출 실적이 없어도 무관", LG_F),
    case("LG2", "1068837", "2026-11-02",
         lg("산업부 수출바우처에 선정된 적이 없습니다. 2025년 3월에 중기부 수출바우처에 선정되었고 협약액 대비 사용률은 정확히 70%였습니다. "
            "채무불이행자로 등록되어 있지만 법원에서 개인회생 변제계획인가를 받았습니다.", debt_default=True, debt_default_exception=True),
         OK, UNKNOWN, [], "사용률 70%는 참여제한 구간(70% 미만) 밖이고 감점 대상일 뿐. 채무불이행은 변제계획인가 단서에 해당", LG_F),
    case("LG3", "1068837", "2026-06-22",
         lg("산업부 수출바우처에 선정된 적이 없습니다. 중기부 수출바우처에 2024년 2월 1일 선정되었고 협약 시작일은 2024년 7월 1일입니다. 바우처 사용률은 69%였습니다."),
         NO, UNKNOWN, ["X6a"], "’24.2.1 당일 선정은 '이후'에 포함. 사용률 70% 미만이고 협약시작일부터 2년이 안 지남", LG_F),
    case("LG4", "1068837", "2026-11-02",
         lg(main_industry_ksic="46331", industry_name="주류 도매업", excluded_industry=True),
         NO, UNKNOWN, ["X11"], "주류 도매업은 표에 中 표기 없이 지원제외 업종으로 적힘", LG_F),
    case("LG5", "1068837", "2026-11-02",
         {k: v for k, v in lg(industry_name="시계 및 귀금속 제품 도매업").items() if k not in ("main_industry_ksic", "excluded_industry")},
         ASK, UNKNOWN, ["X11"], "표의 '46~47 中 사치성 상품 중개업 및 도소매업'은 범위가 정해져 있지 않아 시계 도매업이 드는지 판단 불가", LG_F),
    case("LG6", "1068837", "2026-11-02",
         lg(other="중소기업확인서가 있는 중소기업입니다. 사업자는 이곳 하나입니다. 수출바우처 수행기관으로 참여한 적이 없고 참여 제한을 받은 적도 없습니다. "
                  "수출바우처에 참여한 적은 없습니다. 제 동생이 다른 회사를 운영하는데 그 회사가 올해 수출바우처에 참여하는지는 모릅니다."),
         ASK, UNKNOWN, ["X8"], "가족 운영 기업이 ’26년 참여기업인지 사장님이 확인할 수 없음", LG_F),
]

TP_OK = "중소기업확인서가 있는 중소기업입니다. 은행 연체나 금융거래 문제는 없습니다."


def tp(note="기술보호 바우처에 참여한 적이 없습니다.", **kw):
    # 기술보호 바우처 기본 프로필: 제외 사유가 없는 금속 제조 중소기업.
    p = {"main_industry_ksic": "25112", "industry_name": "금속 구조물 제조업", "employees": 8, "business_status": "정상",
         "tax_arrears": False, "startup_excluded_industry": False, "misuse_history": False, "other": f"{TP_OK} {note}"}
    p.update(kw)
    return p


cases += [
    case("TP1", "1066053", "2026-03-30", tp("2024년 기술보호 바우처에 참여해 끝까지 마쳤습니다."),
         OK, IN_PERIOD, [], "신청기간 마지막 날. 기존 참여기업의 재신청은 가능하고 중도포기가 아님", [AGENCY, EARLY]),
    case("TP2", "1066053", "2026-03-09", tp(employees=2),
         OK, IN_PERIOD, [], "신청기간 첫날. 상시근로자 2명으로 1인기업 아님", [AGENCY, EARLY]),
    case("TP3", "1066053", "2026-03-16",
         tp(main_industry_ksic="10712", industry_name="빵류 제조업", startup_excluded_industry=True,
            note="기술보호 바우처에 참여한 적이 없습니다. 빵 공장이 본업이고 공장 옆에서 작은 카페도 함께 운영합니다."),
         NO, IN_PERIOD, ["X1"], "숙박·음식업을 부수적으로 겸해도 적힌 업종에 해당", [AGENCY, EARLY]),
    case("TP4", "1066053", "2026-11-02", tp("2024년 기술보호 바우처에 참여했다가 중간에 포기했습니다."),
         NO, CLOSED, ["X5"], "종전 사업 중도포기. 기간도 3.30로 마감", [AGENCY]),
    case("TP5", "1066053", "2026-03-16",
         tp(employees=1, note="기술보호 바우처에 참여한 적이 없습니다. 직원 없이 저 혼자 운영합니다."),
         ASK, IN_PERIOD, ["C2"], "1인기업은 본문 제외 목록에 없고 별첨 표에만 있어 제외 여부 판단 불가", [AGENCY, EARLY]),
    case("TP6", "1066053", "2026-03-16",
         tp(other="중소기업확인서가 있는 중소기업입니다. 기술보호 바우처에 참여한 적이 없습니다. 은행 대출 이자가 지금 석 달째 연체 중입니다."),
         ASK, IN_PERIOD, ["X4b"], "'정상인 금융거래가 어려운 경우'의 기준이 없어 연체의 해당 여부 판단 불가", [AGENCY, EARLY]),
]

IV_COMMON = ("대표자와 회사 모두 체납이 없습니다. 혁신바우처 운영기관이 아니고 운영기관과 관계도 없습니다. "
             "올해 이 사업에 선정된 적이 없습니다. 작년에 선정 후 협약을 포기하거나 서비스 계약을 못 한 일도 없습니다.")


def iv(note, **kw):
    # 혁신바우처 기본 프로필: 제외 사유가 없는 제조 소기업. 컨소시엄 상대와 지원 횟수는 사례마다 note에 적는다.
    p = {"applicant_type": "제조 소기업", "main_industry_ksic": "25112", "industry_name": "금속 구조물 제조업", "employees": 15,
         "revenue_3y_avg": 3000000000, "business_status": "정상", "tax_arrears": False, "debt_default": False,
         "excluded_industry": False, "prior_similar_benefit": False, "selected_earlier_round": False, "gov_sanction": False,
         "social_issue": False, "site_region": "부산광역시 사상구", "other": f"{IV_COMMON} {note}"}
    p.update(kw)
    return p


cases += [
    case("IV1", "1066477", "2026-04-03",
         iv("소기업입니다. 강원특별자치도 춘천시의 스타트업 1곳과 저희 회사로 컨소시엄을 구성했고 서로 특수관계는 아닙니다. 혁신바우처는 지금까지 4회 지원받았습니다. 오늘 오후 3시에 신청합니다.",
            revenue_3y_avg=12000000000, site_region="제주특별자치도 서귀포시"),
         OK, IN_PERIOD, [], "C25 평균매출 120억 정각은 이하에 포함. 4회는 5회 미만. 제주는 비수도권 전체와 협업 가능. 마감일 18시 전", [AGENCY]),
    case("IV2", "1066477", "2026-03-20",
         {k: v for k, v in iv("저는 아직 사업자등록이 없는 예비 창업자이고 선정되면 바로 사업자등록을 합니다. 휴업이나 폐업 상태도 아닙니다. 강원특별자치도 춘천시의 제조 소기업 1곳과 컨소시엄을 구성했고 서로 특수관계는 아닙니다. 혁신바우처를 받은 적이 없습니다.",
                               applicant_type="스타트업", site_region="경기도 가평군").items()
          if k not in ("main_industry_ksic", "industry_name", "employees", "revenue_3y_avg", "business_status")},
         OK, IN_PERIOD, [], "스타트업은 예비 창업자 가능. 가평군은 별첨5에 올라 있어 넓게 적힌 쪽 인정. 경기·강원은 경계를 접함. 신청 첫날", [AGENCY]),
    case("IV3", "1066477", "2026-11-02",
         iv("소기업입니다. 경상남도 김해시의 스타트업 1곳과 저희 회사로 컨소시엄을 구성했고 서로 특수관계는 아닙니다. 혁신바우처는 지금까지 5회 지원받았습니다."),
         NO, CLOSED, ["X9"], "총 5회 이상 지원은 제외. 기간도 4.3로 마감", [AGENCY]),
    case("IV4", "1066477", "2026-03-25",
         iv("경상남도 김해시의 스타트업 1곳과 저희 회사로 컨소시엄을 구성했고 서로 특수관계는 아닙니다. 혁신바우처는 받은 적이 없습니다.",
            revenue_3y_avg=12050000000),
         NO, IN_PERIOD, ["A5"], "C25 기준 120억 이하를 초과", [AGENCY]),
    case("IV5", "1066477", "2026-03-25",
         iv("소기업입니다. 대전광역시 유성구의 스타트업 1곳과 저희 회사로 컨소시엄을 구성했고 서로 특수관계는 아닙니다. 혁신바우처는 받은 적이 없습니다. 공장을 대전으로 옮길지 검토 중인데 시기는 아직 못 정했습니다.",
            site_region="서울특별시 금천구"),
         ASK, IN_PERIOD, ["A3a", "A4"], "현재 수도권이고 지역 이전 예정 기업 단서에 드는지 불명. 소재지가 정해져야 인접 여부도 정해짐", [AGENCY]),
    case("IV6", "1066477", "2026-03-25",
         iv("소기업입니다. 경상남도 김해시의 스타트업 1곳과 저희 회사로 컨소시엄을 구성했습니다. 그 스타트업 대표가 제 사촌인데 특수관계에 해당하는지는 모릅니다. 혁신바우처는 받은 적이 없습니다."),
         ASK, IN_PERIOD, ["X6"], "이 공고에 특수관계 정의가 없어 사촌 운영 기업의 해당 여부 판단 불가", [AGENCY]),
]


def bn(note, **kw):
    # 백년소상공인 기본 프로필: 소상공인 규모 안의 음식점.
    p = {"main_industry_ksic": "56111", "industry_name": "한식 일반 음식점업", "employees": 3, "revenue_3y_avg": 400000000,
         "merchant_certificate": True, "business_status": "정상", "tax_arrears": False, "other": note}
    p.update(kw)
    return p


cases += [
    case("BN1", "1069787", "2026-07-29",
         bn("백년가게 지정서의 만료일은 2026년 9월 1일이고 공고 참고1 명단에 저희 업체가 있습니다. 소상공인확인서가 있습니다. 오늘 오전에 신청합니다."),
         OK, IN_PERIOD, [], "만료일 9.1은 대상 구간 첫날. 신청 마감일", [AGENCY]),
    case("BN2", "1069787", "2026-07-14",
         bn("백년소공인 지정서의 만료일은 2026년 11월 30일이고 공고 참고1 명단에 저희 업체가 있습니다. 2024년에 직원이 12명으로 늘어 소상공인 규모를 넘었습니다. 합병은 없었습니다.",
            main_industry_ksic="25112", industry_name="금속 구조물 제조업", employees=12, revenue_3y_avg=3000000000,
            merchant_certificate=False),
         OK, IN_PERIOD, [], "2024년 사유면 2025~2027년 소상공인으로 봄. 신청 첫날", [AGENCY]),
    case("BN3", "1069787", "2026-11-02",
         bn("백년가게 지정서의 만료일은 2026년 8월 31일이고 공고 참고1 명단에 저희 업체가 없습니다. 소상공인확인서가 있습니다."),
         NO, CLOSED, ["A3"], "만료일이 대상 구간 시작 하루 전. 기간도 7.29로 마감", [AGENCY]),
    case("BN4", "1069787", "2026-07-20",
         bn("백년소공인 지정서의 만료일은 2026년 10월이고 공고 참고1 명단에 저희 업체가 있습니다. 2022년에 직원이 12명으로 늘어 소상공인 규모를 넘었습니다. 합병은 없었습니다.",
            main_industry_ksic="25112", industry_name="금속 구조물 제조업", employees=12, revenue_3y_avg=3000000000,
            merchant_certificate=False),
         NO, IN_PERIOD, ["A1", "A2"], "2022년 사유면 유예가 2023~2025년으로 끝나 2026년 신청일에 소상공인이 아님", [AGENCY]),
    case("BN5", "1069787", "2026-07-20",
         bn("백년가게 지정서의 만료일은 2026년 12월 31일인데 공고 참고1 명단에서 저희 업체를 찾지 못했습니다. 소상공인확인서가 있습니다."),
         ASK, IN_PERIOD, ["A3"], "지정서 날짜는 본문 구간 안인데 참고1에 12월 만료 업체가 없어 근거가 충돌", [AGENCY]),
    case("BN6", "1069787", "2026-07-20",
         {k: v for k, v in bn("백년가게 지정서의 만료일은 2026년 11월이고 공고 참고1 명단에 저희 업체가 있습니다. 소상공인 규모는 잘 모르고 확인서는 없습니다.",
                               merchant_certificate=False).items() if k != "employees"},
         ASK, IN_PERIOD, ["A1"], "상시근로자 수 값이 없어 소상공인 여부 판단 불가", [AGENCY]),
]

CASE_NOTE = ("프로필은 전부 가상. 공고마다 일치 2, 불일치 2, 확인 필요 2. PBLN127456은 원문에 본문이 없어 라벨과 사례를 만들지 않음. "
             "expected는 공고를 읽은 사람의 판단이며, 어휘로 못 담는 사실은 프로필 other에 글로 적고 unsupported 조건은 그 글로 판단함. "
             "'_exception' 키는 예외 해당 여부를 입력값으로 밝힌 것. as_of는 2026-11-02 또는 공고 기간 내 날짜. "
             "1066477은 구성기업 한 곳의 입력이며 applicant_type으로 역할을 밝힘. 1069787은 참고1의 실제 업체명을 쓰지 않음.")


# ---------- 인용 확인과 저장 ----------
def pages(notice_id):
    # 쪽 표시 [[pN]]로 원문을 나눈다. 인용은 줄 단위 원문 그대로여야 하므로 정규화하지 않는다.
    out, cur = {}, None
    for line in open(f"{ROOT}/text/holdout4_{notice_id}.txt", encoding="utf-8").read().split("\n"):
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


def check_shape(vocab):
    # 필드가 어휘 안에 있는지, 사례 구성이 2/2/2인지, 프로필 키가 어휘와 보조 키뿐인지 본다.
    aux = {"other", "applicant_type", "industry_name"}
    errs = [(n, c["id"], c["field"]) for n, v in NOTICES.items() for c in v[1] if c["field"] not in vocab]
    for c in cases:
        errs += [(c["id"], k) for k in c["profile"] if k not in vocab and k not in aux and not k.endswith("_exception")]
    for n in NOTICES:
        got = sorted(c["expected"] for c in cases if c["notice_id"] == n)
        if got != sorted([OK, OK, NO, NO, ASK, ASK]):
            errs.append((n, got))
    return errs


def main():
    vocab = json.load(open(f"{LABELS}/fields_vocab.json", encoding="utf-8"))
    errors = [e for n, v in NOTICES.items() for e in check_quotes(n, v[1])] + check_shape(vocab)
    if errors:
        for e in errors:
            print("오류", e)
        sys.exit(1)
    scope = {}
    for n, (desc, conditions, oos, types) in NOTICES.items():
        scope[n] = [desc, types]
        doc = {"source_text": f"holdout4_{n}", "scope": desc, "conditions": conditions, "out_of_scope": oos,
               "notice_id": n, "labeler": LABELER, "status": STATUS}
        json.dump(doc, open(f"{LABELS}/holdout4_{n}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(scope, open(f"{LABELS}/holdout4_scope.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"status": "AI 초안, 참가자 확인 전", "note": CASE_NOTE, "cases": cases},
              open(f"{LABELS}/holdout4_cases.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("인용 확인 통과. 조건", {n: len(v[1]) for n, v in NOTICES.items()}, "사례", len(cases))


if __name__ == "__main__":
    main()
