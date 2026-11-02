"""새 공고(holdout2) 5건의 정답 라벨 작성 스크립트.

흐름: 공고별 조건 정의 → 범위 정의 → 사례 30개 정의 → 인용 문구가 표시 쪽에 있는지 확인 → JSON 저장.
목적: 시스템 출력과 독립적으로, 공고 원문만 읽고 정한 정답을 평가 전에 고정한다.
결과 해석: 파일은 AI 초안이며 참가자 확인 전이다. 인용 확인 통과는 문구 존재만 보장하고 해석의 옳음은 보장하지 않는다.
  판정기 점검(src/check_holdout2_20261102_v1.py)의 불일치는 라벨을 맞추는 신호가 아니라 보고 대상이다.

라벨 작성 원칙.
- 기준서 v7을 따른다. 어휘에 없는 요건은 field=other로 두고, 기관 재량이면 discretionary, 사실 요건이지만 구조화할 수 없으면 unsupported.
- expected는 공고를 읽은 사람의 판단이다. unsupported 요건도 프로필 other 문장으로 사실이 확인되면 충족·위반을 판단한다.
- 인용은 쪽 원문의 한 줄 안에서 글자 그대로 잡는다. 저장 전에 원문 부분 문자열인지 코드로 확인한다.
- 프로필 보조 키: other, {field}_exception, applicant_type, industry_name.

해석 메모(JSON에는 조건별 note 키를 두지 않으므로 여기에 남긴다).
- 1066504 P1: 종료가 '한도 소진 시'뿐이고 날짜가 없다. 기준서 4장 '종료일이 공고에 없으면 일정 확인 필요'를 적용하고 조기 마감을 표시한다.
  같은 장의 '예산 소진이면 공고상 기간 내'는 종료일이 있는 공고에 대한 규칙으로 읽었다. 참가자 확인 항목이다.
- 1066504 B1: '접수일 기준 6개월'은 접수일마다 달라 고정 날짜로 옮길 수 없어 unsupported로 둔다. 사례는 as_of를 접수일로 보고 판단한다.
- 1066504 X2: 붙임3은 이 사업 자체의 보증 제한 목록이다. 정책자금 목록과 같은지 대조하지 않았고, 필드는 어휘상 가장 가까운 excluded_industry를 쓴다.
- 1066504 1쪽 수정 전 값(NICE 595~879, 업력 1년)은 변경 표의 이전 내용이라 조건으로 쓰지 않는다. 충돌이 아니라 대체 관계다.
- 1067320: 신청 주체가 지방자치단체라 사례의 other는 지자체 담당자가 쓴 문장이다. 어휘로 옮길 요건이 없어 전 조건이 unsupported다.
- 1067320: 지방비 50% 매칭과 출자 확약서는 '다음 요건을 모두 충족'의 요건 목록 밖이라 out_of_scope로 둔다. 적격심사에서 필수서류로 보므로 참가자 확인 항목이다.
- 1065015 S3a·S3b: 표는 2026-01-22까지인데 같은 단락은 '창업 기준 충족일'이 공고일 당일 포함이라고 적는다. 2026-01-23 개업만 갈리므로 표기 충돌로 둔다.
  '창업 기준 충족일'을 개업일과 다른 개념으로 읽으면 충돌이 아니라 표가 우선이다. 참가자 확인 항목이다.
- 1065015 E9: '신청 제외 대상'은 마감일 기준이라는 유의사항이 있으나 ⑨는 항목에 '신청일 기준'이 있어 기준서대로 항목을 따른다.
- 1065015: '법인은 법인과 대표자 모두 제외 사유에 해당하지 않아야 함'은 조건을 늘리지 않고, 체납 등 입력값이 양쪽을 함께 묻는 것으로 본다.
- 1065015: 이 원문은 쪽 표시가 [[p1]] 하나뿐이라 모든 근거가 page=1이다.
- PBLN127211: 원문이 신청서·동의서·위임장 서식뿐이고 공고 본문이 없다. 지원대상, 제외, 기간이 없다.
  서식의 제출서류는 요건의 존재만 시사하고 기준값이 없어 unsupported로 둔다. 사업명의 '소상공인'만 profile로 둔다.
  일치 사례는 만들 수 없어 일치 0, 불일치 2, 확인 필요 4로 조정한다.
- PBLN127287 P1: '선착순 접수', '최대 20개 업체 정도'가 있어 기간 안이어도 조기 마감 가능으로 표시한다.
- PBLN127287 X1: 음식점의 주류 판매가 '주류 판매업체'인지 원문으로 정할 수 없다. 사례 TX5의 확인 필요 사유다.
- PBLN127287 C3: '운영 중인'을 business_status eq 정상으로 옮겼다.
"""
import json
import os
import sys

ROOT = os.path.expanduser("~/sosang_agent/data")
LABELS = f"{ROOT}/labels"
LABELER, STATUS = "AI 초안", "참가자 확인 전"
AGENCY = "기관 판단 표시"
CONFLICT = "근거 충돌 표시"
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


# ---------- 1. 비즈플러스카드 개인사업자 (1066504) ----------
# 신용점수·업력·매출·사업자 형태가 지원대상의 네 축이다. 앞의 셋은 어휘에 값 형식이 없어 other로 둔다.
X2_EX = ("붙임3의 '중' 표기는 일부 업종만 제한. 등록 다단계판매, 손해사정·보험대리·핀테크 지원, "
         "부동산 관련 서비스업과 임대차계약 없는 공간대여+부가 서비스는 제외")
c_1066504 = [
    cond("N0", "eligibility", "small_merchant", "derived", True, "not_stated", 3, "①(신용점수) NCB 595점~ 964점인소상공인"),
    other("N1a", "eligibility", "NCB 신용점수 595점 이상 964점 이하", 3, "①(신용점수) NCB 595점~ 964점인소상공인", group="OR:신용점수"),
    other("N1b", "eligibility", "’25.1 이후 특별재해(붙임2) 피해 소상공인으로 NCB 595점 이상", 3,
          "* ‘25.1 이후 특별재해(붙임2)로 피해를 입은 소상공인은 NCB 595점 이상이면 신청 가능", group="OR:신용점수"),
    other("B1", "eligibility", "접수일 기준 업력 6개월 이상", 3, "②(업    력) 접수일기준업력6개월이상인소상공인", basis="application_date"),
    other("R1a", "eligibility", "최근 2개월 매출 200만원 이상", 3, "③(매 출 액) 최근2개월동안200만원이상또는당기부가가치세", group="OR:매출액"),
    other("R1b", "eligibility", "당기 부가가치세 신고매출액 1,200만원 이상", 3, "신고매출액이1,200만원이상인소상공인", group="OR:매출액"),
    other("T1", "eligibility", "개인사업자", 3, "④(사 업 자) 개인사업자"),
    cond("T2", "eligibility", "single_application", "eq", True, "not_stated", 3, "- 1인이다수사업체의대표인경우1곳만신청가능하며공동대표가",
         check="declared", applies_to="다수 사업체 대표"),
    cond("T3", "eligibility", "joint_rep_main", "eq", True, "not_stated", 3, "운영하는사업체는주대표1인만신청가능",
         check="declared", applies_to="공동대표 사업체"),
    other("G1", "eligibility", "본 보증과 재단 기보증, 신·기보 보증금액을 합쳐 8억원 이내", 7, "보증금액을포함하여8억원이내여야하며, 별도한도사정은생략"),
    cond("X1", "exclusion", "business_status", "not_in", ["휴업", "폐업"], "not_stated", 3, "◦휴·폐업중인소상공인"),
    cond("X2", "exclusion", "excluded_industry", "eq", False, "not_stated", 3, "◦보증제한업종에해당하는소상공인(붙임3 참조)", exception=X2_EX),
    cond("X3", "exclusion", "credit_info_listed", "eq", False, "not_stated", 3, "◦연체* 등신용도판단정보를보유한소상공인", check="declared"),
    cond("X4", "exclusion", "tax_arrears", "eq", False, "not_stated", 3, "◦국세나지방세를체납중인소상공인", check="declared"),
    other("D1", "eligibility", "보증심사·카드심사 결과", 7, "1. 보증심사및카드심사결과에따라카드발급이제한될수있습니다.", "discretionary"),
    other("D2", "eligibility", "사업자등록일자와 개업연월일이 다른 경우의 별도 심사 결과", 7, "사업자등록일자와개업연월일간의차이가있을경우별도의심사가", "discretionary"),
    cond("P1", "period", "application_period", "between", ["2026-03-23", None], "as_of_date", 6, "‘26. 3. 23 ~ 한도 소진 시",
         exception="한도 소진 시 종료. 확정 종료일이 없어 조기 마감 가능. 경기지역은 4월 10일(잠정)부터 대면 신청"),
]
oos_1066504 = [
    {"text": "카드 한도·연회비·캐시백·보증료", "reason": "자격이 아니라 지원 내용"},
    {"text": "보증 승인 후 한 달 이내 카드 신청, 앱·대면 접수 경로와 제출 서류", "reason": "자격이 아니라 신청 절차"},
    {"text": "카드심사의 연체·특수채권 보유 심사", "reason": "2단계 카드 심사 항목으로 기준값이 없음. 심사 결과는 D1에 표시"},
]

# ---------- 2. 소공인 인프라시설 고도화 (1067320) ----------
# 신청 주체가 지방자치단체다. 소상공인 어휘가 적용되지 않아 전부 글로 묻는다.
c_1067320 = [
    other("A1", "eligibility", "지방자치단체(지방자치법 제2조제1항)", 1, "나. (지원대상) 다음요건을모두충족하는지방자치단체(「지방자치법」"),
    other("A2a", "eligibility", "소공인 공동기반시설 구축사업(’16~’21년 공고) 선정 이력", 1, "- (사업이력) 중소벤처기업부‘소공인공동기반시설구축사업(’16~‘21년", group="OR:사업이력"),
    other("A2b", "eligibility", "소공인 복합지원센터 구축·운영사업(’19년 이후 공고) 선정 이력", 1, "공고)’ 또는‘소공인복합지원센터구축·운영사업(’19년이후공고)’에", group="OR:사업이력"),
    other("A3", "eligibility", "공고일(2026-04-15) 기준 해당 사업 구축 완료", 1, "- (구축현황) 공고일기준해당사업의구축을완료하였을것", basis="notice_date"),
    cond("P1", "period", "application_period", "between", ["2026-04-15", "2026-04-30T18:00"], "as_of_date", 2, "가. 신청기간: ‘26. 4. 15(수) ~ 4. 30(목), 18:00까지"),
]
oos_1067320 = [
    {"text": "국비 50%·지방비 50% 매칭, 지자체 출자 확약서, 신청 전 타당성 검토", "reason": "지원대상 요건 목록 밖의 지원 방식·제출 서류"},
    {"text": "현장·발표 평가 항목과 구축 연도 가점", "reason": "자격이 아니라 선정 평가"},
    {"text": "사업기간 내 고도화 완료, 소공인 수요 자료·장비 도입 위원회 계획 반영", "reason": "선정 후 의무와 사업계획서 작성 사항"},
]

# ---------- 3. 초기창업패키지 일반형 (1065015) ----------
# 제외 사유 기준일은 마감일이고 ⑨만 신청일이다. 이 원문은 쪽 표시가 하나뿐이다.
DEBT_EX = ("마감일 기준 채무변제 완료, 프리워크아웃·개인워크아웃·새출발기금 채무조정합의, 회생계획·변제계획 인가, 파산 면책 확정, "
           "재기지원보증·재창업 자금지원")
TAX_EX = "마감일 기준 강제징수·체납처분 유예, 특수채무 변제 증빙"
RECOUP_EX = "마감일까지 전액 반환, 회생·파산 면책결정, 분할납부 승인 후 정상납부"
PRIOR_EX = "글로벌기업 협업 프로그램(’19~’20년 창구, ’20년 마중, 정글, 엔업)과 창업도약패키지 성장촉진 프로그램(’17~’21년)만 지원받은 경우 신청 가능"
CUR_EX = "공고사업과 동일연도 창업사업화 지원사업이 아닌 경우, 지자체 지원사업은 협약 잔여기간과 관계없이 신청 가능"
c_1065015 = [
    other("S1", "eligibility", "중소기업기본법상 중소기업의 대표자", 1, "◦ ｢중소기업기본법｣ 제2조 제1호에 따른 중소기업의 대표자이자, ｢중소기업창업 지원법｣ 제2조제2호부터 제2조제3의2까지의 각 호의 정의에 따른 창업기업의 대표자로서 모집공고일 기준 창업 3년 이내인 자"),
    other("S2", "eligibility", "중소기업창업 지원법상 창업기업의 대표자", 1, "◦ ｢중소기업기본법｣ 제2조 제1호에 따른 중소기업의 대표자이자, ｢중소기업창업 지원법｣ 제2조제2호부터 제2조제3의2까지의 각 호의 정의에 따른 창업기업의 대표자로서 모집공고일 기준 창업 3년 이내인 자", basis="notice_date"),
    cond("S3a", "eligibility", "founded_date", "between", ["2023-01-23", "2026-01-22"], "notice_date", 1, "▶ 신청가능 업력 : 2023년 1월 23일 ~ 2026년 1월 22일", "OR:업력"),
    cond("S3b", "eligibility", "founded_date", "between", ["2023-01-23", "2026-01-23"], "notice_date", 1, "창업  기준 충족일이 모집공고일 이전일 것 (모집공고일 당일 포함)", "OR:업력", "conflict"),
    cond("S4", "eligibility", "business_registration", "eq", True, "not_stated", 1, "* 개인‧법인사업자 모두 사업 개시 및 사업자 등록을 완료하여야 함"),
    cond("S5", "eligibility", "all_reps_eligible", "eq", True, "not_stated", 1, "• 공동대표 또는 각자대표로 구성된 기업의 경우, 대표자 전원이 ‘신청자격’에 해당되고, ‘신청 제외 대상’에 해당되지 않아야 함",
         check="declared", applies_to="공동·각자대표 기업"),
    other("S6", "eligibility", "다수 사업자등록증 보유 시 창업 여부 기준표(붙임2)상 창업", 1, "• 다수의 사업자등록증(개인‧법인)을 보유한 경우, 창업여부 기준표에 따라 신청 자격 적합 여부 결정([붙임 2] 창업 여부 기준표를 참고하여 신청 전 필히 확인)",
          applies_to="다수 사업자 보유자"),
    cond("S7", "eligibility", "head_office", "eq", True, "not_stated", 1, "• 본점과 지점이 있는 경우 본점 사업자로만 신청 가능하며, 중복 신청한 경우 본점을 기준으로 요건 검토 예정",
         check="declared", applies_to="본점·지점 보유 기업"),
    cond("E1", "exclusion", "debt_default", "eq", False, "deadline_date", 1, "① 금융기관 등으로부터 채무불이행으로 규제 중인 자(기업)", check="declared", exception=DEBT_EX),
    cond("E2", "exclusion", "tax_arrears", "eq", False, "deadline_date", 1, "② 국세 또는 지방세 체납 중인 자(기업)", check="declared", exception=TAX_EX),
    cond("E3", "exclusion", "recoup_outstanding", "eq", False, "deadline_date", 1, "③ 창업진흥원으로부터 발생한 환수금등의 반환이 종결되지 않은 자(기업)", check="declared", exception=RECOUP_EX),
    cond("E4", "exclusion", "startup_excluded_industry", "eq", False, "deadline_date", 1, "④ 「중소기업창업 지원법 시행령」 제4조(창업에서 제외되는 업종)의 업종을 영위하고 있거나 영위하고자 하는 자(기업) ([붙임 3] 지원 제외 대상 업종 참조)"),
    other("E5", "exclusion", "붙임4-1 창업사업화 지원사업에 총 3회 이상 협약 이력 없음(중단 포함)", 1, "⑤ 중소벤처기업부 창업사업화 지원사업[붙임4-1]에 총 3회 이상 선정되어 협약을 체결했던 이력이 있는 자(기업)   ※ 중단(중단처분·중도포기자) 포함", basis="deadline_date"),
    cond("E6", "exclusion", "prior_restart_program", "eq", False, "deadline_date", 1, "⑥ 사업연도를 불문하고, [붙임4-2]에 명시된 사업에 선정되어 협약을 체결했던 이력이 있는 자(기업)   ※ 중단(중단처분·중도포기자) 포함", check="declared", exception=PRIOR_EX),
    cond("E7", "exclusion", "current_startup_program", "eq", False, "deadline_date", 1, "⑦ 2026년 중소벤처기업부 및 타 중앙정부·공공기관의 ‘창업사업화 지원사업*’에 선정되어 사업을 수행 중인 자(기업),[붙임5] 참고   ※ 중단(중단처분·중도포기자) 포함", check="declared", exception=CUR_EX),
    cond("E8", "exclusion", "gov_sanction", "eq", False, "deadline_date", 1, "⑧ 중소벤처기업부 창업지원사업에 참여 제한으로 제재 중인 자", check="declared"),
    cond("E9", "exclusion", "business_status", "not_in", ["휴업", "폐업"], "application_date", 1, "⑨ 신청일 기준 동 사업에 신청하는 사업자가 휴‧폐업 중인 자(기업)  ※ 해당시"),
    cond("E10", "exclusion", "bank_account_available", "eq", True, "deadline_date", 1, "⑩ 창업진흥원이 지정한 은행 계좌(사업비 계좌) 개설 및 거래가 불가한 자(기업)", check="declared"),
    cond("E11", "exclusion", "program_staff", "eq", False, "deadline_date", 1, "⑪ 2026년 동 사업 주관기관의 전담조직의 장, 전담/겸직인력으로 참여 중 또는 참여 예정인 자(기업)", check="declared"),
    cond("E12", "exclusion", "wage_arrears_listed", "eq", False, "deadline_date", 1, "⑫ 「근로기준법」에 따라 고용노동부가 공개하는 체불사업주 명단에 포함된 자(기업)", check="declared"),
    cond("E13", "exclusion", "subsidy_excluded", "eq", False, "deadline_date", 1, "⑬ 「보조금 관리에 관한 법률」 제31조의2(보조사업 수행 배제 등)에 따라 수행대상에서 배제된 자(기업)", check="declared"),
    other("E14", "exclusion", "장관이 인정하는 참여 제한 사유 해당 여부", 1, "⑭ 기타 중소벤처기업부 장관이 참여를 제한할 정당한 사유가 있다고 인정하는 자(기업)", "discretionary", basis="deadline_date"),
    cond("P1", "period", "application_period", "between", ["2026-01-23", "2026-02-13T16:00"], "as_of_date", 1, "□ 접수 기간 : ’26년1월23일(금) ~ 2월 13일(금), 16:00까지"),
]
oos_1065015 = [
    {"text": "딥테크 특화형·투자연계형", "reason": "유형별 별도 공고"},
    {"text": "본점 소재 권역의 주관기관 1개 선택, 대표자 본인 신청, 공고 양식 사업계획서", "reason": "자격이 아니라 신청 절차"},
    {"text": "서류평가 가점·면제·우선 선정, 평가 단계 60점 기준", "reason": "자격이 아니라 선정 평가"},
    {"text": "평가위원 참여 불가, 국외 창업의 사업비 집행 가능 여부, 협약 후 창업 유지 의무", "reason": "신청 자격 표 밖의 유의사항과 선정 후 의무"},
]

# ---------- 4. 평창군 세무서비스 수수료 지원 (PBLN127211) ----------
# 원문이 서식뿐이다. 제출서류로 시사되는 요건은 기준값이 없어 묻는 내용만 글로 적는다.
c_PBLN127211 = [
    cond("W1", "eligibility", "small_merchant", "derived", True, "not_stated", 1, "2026년 평창군 「소상공인 세무서비스 수수료 지원사업」 신청서"),
    other("W2", "eligibility", "공고 본문의 지원대상·제외 기준(제공된 원문은 서식만 있음)", 1, "소상공인 세무서비스 수수료 지원사업 신청서 및 개인정보 제공 동의서"),
    other("W3", "eligibility", "평창군 사업장·주소 등 지역 요건(기준 없음)", 1, "③ 주민등록 초본(주소이력 포함)"),
    other("W4", "eligibility", "2025년 매출 기준(증빙만 요구, 기준값 없음)", 1, "전년도(2025년) 매출액 증빙서류(부가가치세 과세표준증명원 등)"),
    other("W5", "eligibility", "세무사·회계사 세무서비스 이용과 수수료 지급(증빙만 요구, 기간·금액 기준 없음)", 1, "세무사(회계사) 이용 증빙서류"),
    other("W6", "eligibility", "상시근로자 기준(판단서류만 요구, 기준값 없음)", 1, "상시근로자 판단서류"),
    other("W7", "exclusion", "국세·지방세 체납 관련 요건(납세증명서만 요구, 제외 문구 없음)", 1, "⑤ 국세 및 지방세 납세증명서 각 1부"),
    cond("P1", "period", "application_period", "between", [None, None], "not_stated", 1, "2026년    월     일", check="unsupported"),
]
oos_PBLN127211 = [
    {"text": "평창사랑상품권 가맹 여부 기입란", "reason": "서식 기입 항목일 뿐 요건이라는 문구가 없음"},
    {"text": "개인정보 동의서, 통합위임장, 통장사본, 신분증", "reason": "자격이 아니라 신청 절차"},
]

# ---------- 5. 포항시 택시지붕광고 (PBLN127287) ----------
# 업체 자격과 광고 내용 제한을 나눈다. 선정기준의 적합성·종합 고려는 재량이다.
PH_ELIG = "2. 신청자격 : 포항시 관내에서 사업장을 운영 중인 소상공인"
PH_BAN = "※ 주류 및 담배(전자담배 포함) 제조·판매업체와 관련 광고는 신청 불가"
c_PBLN127287 = [
    cond("C1", "eligibility", "small_merchant", "derived", True, "not_stated", 1, PH_ELIG),
    cond("C2", "eligibility", "site_region", "eq", "포항시", "not_stated", 1, PH_ELIG),
    cond("C3", "eligibility", "business_status", "eq", "정상", "not_stated", 1, PH_ELIG),
    other("X1", "exclusion", "주류·담배(전자담배 포함) 제조·판매업체 아님", 1, PH_BAN),
    other("X2", "exclusion", "주류·담배 관련 광고 아님", 1, PH_BAN),
    other("D1", "eligibility", "광고 내용의 적합성과 송출 가능 여부", 1, "○ 광고 내용의 적합성 및 광고 송출 가능 여부", "discretionary"),
    other("D2", "eligibility", "접수 순서와 광고매체 운영 여건의 종합 고려", 1, "○ 접수 순서 및 광고매체 운영 여건 등을 종합적으로 고려", "discretionary"),
    cond("P1", "period", "application_period", "between", ["2026-10-14", "2026-11-30"], "as_of_date", 1, "가. 접수기간 : 2026. 10. 14.(수) ~ 11. 30.(월)",
         exception="선착순 접수, 최대 20개 업체 정도라 조기 마감 가능"),
]
oos_PBLN127287 = [
    {"text": "광고 매체·형태·기간(2026-12-31까지)과 송출 순서", "reason": "자격이 아니라 지원 내용"},
    {"text": "온라인 신청서, 접수확인 전화, 상호·사진·로고 자료", "reason": "자격이 아니라 신청 절차"},
    {"text": "사실과 다른 신청의 선정 취소", "reason": "선정 후 조치"},
]

NOTICES = {
    "1066504": ("개인사업자 소상공인의 지원 요건과 제한사항(1단계 보증 신청 기준)", c_1066504, oos_1066504, ["공동대표 사업체", "다수 사업체 대표"]),
    "1067320": ("지방자치단체의 사업 이력·구축 현황 요건", c_1067320, oos_1067320, []),
    "1065015": ("일반형 창업기업 대표자의 신청 자격과 신청 제외", c_1065015, oos_1065015, ["공동·각자대표 기업", "다수 사업자 보유자", "본점·지점 보유 기업"]),
    "PBLN127211": ("서식에서 확인되는 사업명과 제출서류 항목. 공고 본문 없음", c_PBLN127211, oos_PBLN127211, []),
    "PBLN127287": ("포항시 관내 소상공인의 신청 자격과 신청 불가 업종·광고", c_PBLN127287, oos_PBLN127287, []),
}


# ---------- 사례 ----------
def case(id, notice_id, as_of, profile, expected, period, decisive, reason, flags):
    return {"id": id, "notice_id": notice_id, "program": None, "as_of": as_of, "profile": profile,
            "expected": expected, "period_status": period, "decisive": decisive, "reason": reason, "flags": list(flags)}


# 비즈플러스: 964·965 경계, 특재 예외, 매출 OR, 6개월 정각, 붙임3 예외가 어려운 지점이다.
BZ_FLAGS = (AGENCY, EARLY)
BZ_REST = "개인사업자입니다. 다른 사업체는 없고 공동대표도 아닙니다. 지금까지 받은 보증은 없습니다."


def bz(**k):
    p = {"main_industry_ksic": "56111", "industry_name": "한식 일반 음식점업", "employees": 2, "revenue_3y_avg": 120000000,
         "founded_date": "2019-05-02", "business_status": "정상", "tax_arrears": False, "credit_info_listed": False}
    p.update(k)
    return p


cases = [
    case("BZ1", "1066504", "2026-04-20",
         bz(founded_date="2025-10-20", other=f"{BZ_REST} 신용점수는 NCB 964점입니다. 최근 2개월 매출은 350만원입니다. 오늘 보증 신청을 합니다."),
         OK, UNKNOWN, [], "4.20 접수면 업력 6개월 정각, NCB 964는 상한 포함. 수정 전 값(879점, 1년)이면 떨어지는 사례", BZ_FLAGS),
    case("BZ2", "1066504", "2026-11-02",
         bz(site_region="경상북도 의성군", other=f"{BZ_REST} 신용점수는 NCB 970점입니다. 2025년 3월 의성 산불로 가게가 피해를 입었습니다. 최근 2개월 매출은 150만원이고 이번 부가세 신고 매출은 1,200만원입니다."),
         OK, UNKNOWN, [], "964 초과지만 붙임2 지역 특별재해 피해라 595 이상이면 됨. 2개월 매출은 미달, 신고매출 1,200만원 정각으로 OR 충족", BZ_FLAGS),
    case("BZ3", "1066504", "2026-11-02",
         bz(other=f"{BZ_REST} 신용점수는 NCB 965점입니다. 재해 피해를 입은 적은 없습니다. 최근 2개월 매출은 400만원입니다."),
         NO, UNKNOWN, ["N1a", "N1b"], "965는 상한 964 초과, 특별재해 예외 없음", BZ_FLAGS),
    case("BZ4", "1066504", "2026-11-02",
         bz(main_industry_ksic="46333", industry_name="담배 도매업", other=f"{BZ_REST} 신용점수는 NCB 800점입니다. 최근 2개월 매출은 600만원입니다."),
         NO, UNKNOWN, ["X2"], "46333은 붙임3에 '중' 표기 없이 전부 제한", BZ_FLAGS),
    case("BZ5", "1066504", "2026-11-02",
         bz(other=f"{BZ_REST} 신용점수는 아직 조회해 보지 않았습니다. 최근 2개월 매출은 300만원입니다."),
         ASK, UNKNOWN, ["N1a", "N1b"], "신용점수 값 없음", BZ_FLAGS),
    case("BZ6", "1066504", "2026-11-02",
         bz(main_industry_ksic="68112", industry_name="비주거용 건물 임대업",
            other=f"{BZ_REST} 신용점수는 NCB 800점입니다. 최근 2개월 매출은 300만원입니다. 시간 단위로 회의실을 빌려줍니다. 손님과 임대차계약을 맺는지, 다른 서비스를 함께 제공하는지는 아직 정하지 않았습니다."),
         ASK, UNKNOWN, ["X2"], "부동산업은 제한이나 68112 공간대여는 임대차계약 없음·부가 서비스 제공 시 예외. 해당 여부 불명", BZ_FLAGS),
]

# 소공인 인프라: 공고일 당일 준공, '19년 공고 경계, 민간 신청, 부분 준공이 어려운 지점이다.
cases += [
    case("IF1", "1067320", "2026-04-20",
         {"other": "저희는 기초자치단체 구청입니다. 2019년 공고된 소공인 공동기반시설 구축사업에 선정되었고 시설은 2021년 5월에 준공했습니다."},
         OK, IN_PERIOD, [], "지자체, ’16~’21년 공고 범위, 공고일 전 준공", ()),
    case("IF2", "1067320", "2026-04-30",
         {"other": "저희는 광역시입니다. 2019년 공고된 소공인 복합지원센터 구축·운영사업에 선정되었고 2026년 4월 15일에 준공했습니다."},
         OK, IN_PERIOD, [], "’19년 공고는 '이후'에 포함, 공고일 당일 준공은 공고일 기준 완료. 마감 당일", ()),
    case("IF3", "1067320", "2026-04-20",
         {"other": "금속 가공 공방을 하는 소공인입니다. 저희 공방이 쓰는 공동기반시설의 장비를 바꾸고 싶어 직접 신청하려고 합니다."},
         NO, IN_PERIOD, ["A1"], "신청 주체는 지방자치단체. 시설 이용 소공인은 대상 아님", ()),
    case("IF4", "1067320", "2026-04-20",
         {"other": "저희는 기초자치단체 시청입니다. 2023년 공고된 소공인 복합지원센터 구축·운영사업에 선정되었고 준공일은 2026년 4월 16일로 잡혀 있습니다."},
         NO, IN_PERIOD, ["A3"], "공고일 다음 날 준공이라 공고일 기준 구축 미완료", ()),
    case("IF5", "1067320", "2026-11-02",
         {"other": "저희는 기초자치단체 구청입니다. 2020년 공고된 소공인 공동기반시설 구축사업에 선정되었습니다."},
         ASK, CLOSED, ["A3"], "구축 완료 여부 값 없음. 기간은 마감", ()),
    case("IF6", "1067320", "2026-04-20",
         {"other": "저희는 기초자치단체 시청입니다. 2021년 공고된 소공인 공동기반시설 구축사업에 선정되었습니다. 1층 공용장비실은 2024년에 준공해 운영 중이고, 계획에 있던 2층 시설은 2026년 7월 준공 예정입니다."},
         ASK, IN_PERIOD, ["A3"], "일부 시설만 준공. '구축 완료'가 사업 전체인지 원문으로 판단 불가", ()),
]


# 초기창업: 1.22·1.23 업력 경계, 마감일 기준 예외, 중도포기 포함, 기준표 판정이 어려운 지점이다.
SP_REST = "중소기업 대표로 창업기업에 해당합니다. 다른 사업자등록은 없습니다. 창업사업화 지원사업에 협약한 이력은 없습니다."


def sp(**k):
    p = {"founded_date": "2025-03-03", "business_registration": True, "main_industry_ksic": "58222", "industry_name": "응용 소프트웨어 개발 및 공급업",
         "business_status": "정상", "debt_default": False, "tax_arrears": False, "recoup_outstanding": False, "startup_excluded_industry": False,
         "prior_restart_program": False, "current_startup_program": False, "gov_sanction": False, "bank_account_available": True,
         "program_staff": False, "wage_arrears_listed": False, "subsidy_excluded": False, "other": SP_REST}
    p.update(k)
    return p


cases += [
    case("SP1", "1065015", "2026-02-13", sp(founded_date="2023-01-23"), OK, IN_PERIOD, [],
         "2023-01-23은 신청가능 업력 첫날. 마감 당일", (AGENCY,)),
    case("SP2", "1065015", "2026-02-13",
         sp(debt_default=True, debt_default_exception=True,
            other=SP_REST + " 금융기관 채무불이행이 있었지만 오늘(2026년 2월 13일) 법원에서 변제계획 인가를 받았습니다."),
         OK, IN_PERIOD, [], "채무불이행이나 마감일(2.13) 기준 변제계획 인가로 예외 해당", (AGENCY,)),
    case("SP3", "1065015", "2026-02-01", sp(founded_date="2023-01-22"), NO, IN_PERIOD, ["S3a", "S3b"],
         "2023-01-22 개업은 신청가능 업력 시작일 하루 전", (AGENCY,)),
    case("SP4", "1065015", "2026-02-01",
         sp(prior_restart_program=True, prior_restart_program_exception=False,
            other="중소기업 대표로 창업기업에 해당합니다. 다른 사업자등록은 없습니다. 2024년 창업중심대학(초기 창업기업)에 선정되어 협약했다가 중도 포기했습니다."),
         NO, IN_PERIOD, ["E6"], "붙임4-2 사업 협약 이력은 사업연도 불문, 중도포기 포함", (AGENCY,)),
    case("SP5", "1065015", "2026-02-01", sp(founded_date="2026-01-23"), ASK, IN_PERIOD, ["S3a", "S3b"],
         "표는 1.22까지, 같은 단락의 충족일 문구는 공고일 당일 포함이라 공고일 개업이 갈림", (AGENCY, CONFLICT)),
    case("SP6", "1065015", "2026-11-02",
         sp(applicant_type="다수 사업자 보유자",
            other="중소기업 대표로 창업기업에 해당합니다. 개인사업자를 계속 운영하면서 같은 업종의 법인을 새로 세워 그 법인으로 신청합니다. 제 지분과 친족 지분을 합친 비율은 아직 확인하지 못했습니다. 창업사업화 지원사업에 협약한 이력은 없습니다."),
         ASK, CLOSED, ["S6"], "기준표는 동종 법인이면 지분 50% 초과·최대주주 여부로 갈리는데 지분 값 없음. 기간은 마감", (AGENCY,)),
]

# 평창: 서식만 있어 일치를 확정할 수 없다. 소상공인 수치 위반만 불일치로 둔다.
PC_FULL = "평창군에 사업장이 있고 주소도 평창입니다. 세무사에게 맡겨 수수료를 냈습니다. 세금 체납은 없습니다."


def pc(**k):
    p = {"main_industry_ksic": "56111", "industry_name": "한식 일반 음식점업", "employees": 2, "revenue_3y_avg": 120000000,
         "revenue_prev_year": 120000000, "tax_arrears": False, "site_region": "강원특별자치도 평창군", "other": PC_FULL}
    p.update(k)
    return p


cases += [
    case("PC1", "PBLN127211", "2026-11-02",
         pc(main_industry_ksic="10712", industry_name="떡류 제조업", employees=10, other="저를 빼고 직원이 10명입니다. " + PC_FULL),
         NO, UNKNOWN, ["W1"], "서식이 대표자 제외로 세는 상시근로자 10명. 제조업 소상공인 기준 10명 미만 위반", ()),
    case("PC2", "PBLN127211", "2026-11-02",
         pc(main_industry_ksic="96112", industry_name="두발 미용업", employees=5, other="저를 빼고 직원이 5명입니다. " + PC_FULL),
         NO, UNKNOWN, ["W1"], "미용업 소상공인 기준 5명 미만 위반", ()),
    case("PC3", "PBLN127211", "2026-11-02", pc(), ASK, UNKNOWN, ["W2"],
         "알려진 사실은 모두 무난하나 공고 본문이 없어 지원대상·제외 기준을 대조할 수 없음", ()),
    case("PC4", "PBLN127211", "2026-11-02",
         pc(other="평창군에 사업장이 있고 주소도 평창입니다. 세금 체납은 없습니다. 세무사와 올해 계약했지만 수수료는 아직 내지 않았습니다."),
         ASK, UNKNOWN, ["W5"], "수수료 지급 시점 기준이 원문에 없음", ()),
    case("PC5", "PBLN127211", "2026-11-02", pc(revenue_prev_year=900000000, revenue_3y_avg=900000000), ASK, UNKNOWN, ["W4"],
         "매출 증빙만 요구하고 기준값이 없음", ()),
    case("PC6", "PBLN127211", "2026-11-02",
         pc(other="사업장은 평창군인데 제 주소지는 강릉시입니다. 세무사에게 맡겨 수수료를 냈습니다. 세금 체납은 없습니다."),
         ASK, UNKNOWN, ["W3"], "주소 이력 서류만 있고 주소 요건 유무가 없음", ()),
]


# 포항: 경계는 상시근로자 수와 사업장 소재지, 해석 지점은 음식점의 주류 판매다.
TX_FLAGS = (AGENCY, EARLY)
TX_CLEAN = "술과 담배는 팔지 않습니다. 광고에는 저희 상호와 대표 사진을 넣습니다."


def tx(**k):
    p = {"site_region": "경상북도 포항시 남구", "business_status": "정상", "main_industry_ksic": "96112", "industry_name": "두발 미용업",
         "employees": 4, "revenue_3y_avg": 90000000, "other": TX_CLEAN}
    p.update(k)
    return p


cases += [
    case("TX1", "PBLN127287", "2026-11-02", tx(), OK, IN_PERIOD, [], "미용업 4명은 5명 미만. 포항 사업장 운영 중", TX_FLAGS),
    case("TX2", "PBLN127287", "2026-11-30",
         tx(main_industry_ksic="10712", industry_name="떡류 제조업", employees=9, revenue_3y_avg=300000000, site_region="경상북도 포항시 북구"),
         OK, IN_PERIOD, [], "제조업 9명은 10명 미만. 마감 당일", TX_FLAGS),
    case("TX3", "PBLN127287", "2026-11-02",
         tx(main_industry_ksic="46333", industry_name="담배 도매업", other="담배 도매업체입니다. 광고에는 저희 상호만 넣을 생각입니다."),
         NO, IN_PERIOD, ["X1"], "담배 판매업체는 광고 내용과 관계없이 신청 불가", TX_FLAGS),
    case("TX4", "PBLN127287", "2026-11-02", tx(site_region="경상북도 경주시"), NO, IN_PERIOD, ["C2"],
         "사업장이 포항시 관내가 아님", TX_FLAGS),
    case("TX5", "PBLN127287", "2026-11-02",
         tx(main_industry_ksic="56111", industry_name="한식 일반 음식점업", employees=3,
            other="한식 음식점이고 손님에게 소주와 맥주도 팝니다. 광고에는 음식 사진만 넣습니다."),
         ASK, IN_PERIOD, ["X1"], "음식점의 주류 판매가 '주류 판매업체'에 드는지 원문으로 판단 불가", TX_FLAGS),
    case("TX6", "PBLN127287", "2026-11-02",
         {k: v for k, v in tx().items() if k != "employees"}, ASK, IN_PERIOD, ["C1"],
         "상시근로자 수 값 없음", TX_FLAGS),
]

CASE_NOTE = ("프로필은 전부 가상. 공고마다 일치 2, 불일치 2, 확인 필요 2로 구성하되 PBLN127211은 조정함: "
             "원문이 서식뿐이고 공고 본문이 없어 필수 요건을 모두 대조한 일치를 정할 수 없으므로 일치 0, 불일치 2, 확인 필요 4. "
             "expected는 공고를 읽은 사람의 판단이며, 어휘로 못 담는 사실은 프로필 other에 글로 적고 unsupported 조건은 그 글로 판단함. "
             "'_exception' 키는 예외 해당 여부를 입력값으로 밝힌 것. as_of는 2026-11-02 또는 공고 기간 내 날짜. "
             "1067320 프로필의 other는 신청 주체인 지자체 담당자 문장이며, IF3만 소공인 사장 문장.")


# ---------- 인용 확인과 저장 ----------
def pages(notice_id):
    # 쪽 표시 [[pN]]로 원문을 나눈다. 인용은 줄 단위 원문 그대로여야 하므로 정규화하지 않는다.
    out, cur = {}, None
    for line in open(f"{ROOT}/text/holdout2_{notice_id}.txt", encoding="utf-8").read().split("\n"):
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
        doc = {"source_text": f"holdout2_{n}", "scope": desc, "conditions": conditions, "out_of_scope": oos,
               "notice_id": n, "labeler": LABELER, "status": STATUS}
        json.dump(doc, open(f"{LABELS}/holdout2_{n}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(scope, open(f"{LABELS}/holdout2_scope.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"status": "AI 초안, 참가자 확인 전", "note": CASE_NOTE, "cases": cases},
              open(f"{LABELS}/holdout2_cases.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("인용 확인 통과. 조건", {n: len(v[1]) for n, v in NOTICES.items()}, "사례", len(cases))


if __name__ == "__main__":
    main()
