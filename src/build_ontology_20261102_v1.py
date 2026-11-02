"""온톨로지 생성 스크립트.

흐름: 공고 원문에서 확인한 업종 계층·소상공인 규모 기준·제외 업종을 Turtle로 저장 → SHACL 규칙 저장 → 공고별 제외 목록 일치 검사.
목적: 여러 공고가 공유하는 개념(소상공인, 제외 업종)을 한곳에 두고 출처를 달아, 공고 간 차이를 판정에서 드러낸다.
결과 해석: 규모 기준의 출처가 여러 개이면 판정기가 출처별로 모두 계산한다. 결과가 갈리면 '확인 필요'가 된다.
"""
import os, re

R = os.path.expanduser("~/sosang_agent")
P = """@prefix sa: <https://sosang.example/ontology#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
"""
SECTIONS = {"A": (1, 3), "B": (5, 8), "C": (10, 34), "D": (35, 35), "E": (36, 39), "F": (41, 42), "G": (45, 47), "H": (49, 52), "I": (55, 56), "J": (58, 63),
            "K": (64, 66), "L": (68, 68), "M": (70, 73), "N": (74, 76), "O": (84, 84), "P": (85, 85), "Q": (86, 87), "R": (90, 91), "S": (94, 96), "T": (97, 98), "U": (99, 99)}

# 업종별 소기업 평균매출액 기준(억원). 공고마다 표가 달라 출처별로 분리해 저장한다.
SIZE_LIVING = {"C19": 140, "C24": 140, "C10": 120, "C11": 120, "C14": 120, "C15": 120, "C20": 120, "C21": 120, "C23": 120, "C25": 120, "C26": 120, "C28": 120, "C29": 120, "C30": 120,
               "C32": 120, "D": 120, "E36": 120, "H": 100, "K": 100, "A": 80, "B": 80, "C12": 80, "C13": 80, "C16": 80, "C17": 80, "C18": 80, "C22": 80, "C27": 80, "C31": 80, "C33": 80,
               "F": 80, "G": 60, "J": 50, "E": 40, "L": 40, "M": 30, "N": 30, "R": 30, "C34": 15, "I": 15, "P": 15, "Q": 15, "S": 15}
SIZE_INSURANCE = {"I": 10, "S": 10, "G": 50, "A": 80, "B": 80, "F": 80, "H": 80, "C10": 120, "C14": 120, "C32": 120, "C28": 120}
SIZE_MARKET = {"C10": 120, "C11": 120, "C14": 120, "C15": 120, "C19": 120, "C20": 120, "C21": 120, "C23": 120, "C24": 120, "C25": 120, "C26": 120, "C28": 120, "C29": 120, "C30": 120, "C32": 120,
               "C12": 80, "C13": 80, "C16": 80, "C17": 80, "C18": 80, "C22": 80, "C27": 80, "C31": 80, "C33": 80, "C34": 10}
SOURCES = {"LIVING": ("생활문화 공고 제2026-325호 붙임1", SIZE_LIVING), "INSURANCE": ("고용보험료 공고 제2025-660호", SIZE_INSURANCE), "MARKET": ("판로개척 공고 제2026-397호 참고4", SIZE_MARKET)}

# 제외 업종 목록: 정책자금 변경 5차 별표1. partial=True는 원문의 "코드 중"(해당 코드의 일부 업종만 제외).
EXCL = [("33409", True, "도박기계 및 사행성, 불건전 오락기구 제조업"), ("46102", True, "담배 중개업"), ("46209", True, "잎담배 도매업"), ("46333", False, "담배 도매업"),
        ("46463", True, "도박기계 및 사행성, 불건전 오락기구 도매업"), ("47640", True, "도박기계 및 사행성, 불건전 오락기구 소매업"), ("47811", True, "약국, 한약국"), ("47859", True, "성인용품 판매점"),
        ("47911", True, "도박기계·성인용품 소매 및 중개"), ("47912", True, "도박기계·성인용품 소매 및 중개"), ("47993", True, "다단계 방문판매"), ("52991", True, "통관업"), ("56211", False, "일반유흥주점업"),
        ("56212", False, "무도유흥주점업"), ("5821", True, "도박 및 사행성, 불건전 게임 S/W"), ("63992", False, "가상자산 매매 및 중개업"), ("63999", True, "온라인게임 아이템 중개업"), ("64", False, "금융업"),
        ("65", False, "보험 및 연금업"), ("66", False, "금융 및 보험관련 서비스업"), ("68", False, "부동산업"), ("76390", True, "불건전 오락기구 임대업"), ("711", False, "법무 관련 서비스업"), ("712", False, "회계 및 세무 관련 서비스업"),
        ("731", False, "수의업"), ("73904", True, "감정평가업"), ("75330", True, "흥신소"), ("75993", False, "신용조사 및 추심대행업"), ("75999", True, "경품용 상품권 발행·판매"), ("86", False, "보건업"),
        ("91113", False, "경주장 및 동물 경기장 운영업"), ("91121", False, "골프장 운영업"), ("9122", True, "성인용게임장 등"), ("91242", False, "카지노 운영업"), ("91249", False, "기타 사행시설 관리 및 운영업"),
        ("91291", False, "무도장 운영업"), ("9612", True, "증기탕 및 안마시술소"), ("96992", False, "점술 및 유사서비스업"), ("96999", True, "휴게텔, 키스방, 대화방")]
# 예외: allow=항상 허용, conditional=추가 사실이 있어야 허용(필드명). 원문 근거는 별표1과 자금별 신청대상.
EXCEPTIONS = [("6821", "allow", None, "부동산관리업"), ("68221", "conditional", "same_site_6m", "동일 장소 6개월 이상 부동산 중개·대리업"), ("68224", "conditional", "same_site_6m", "동일 장소 6개월 이상 분양 대행업"),
              ("68112", "conditional", "shared_office", "공유오피스·공유주방 영위"), ("68112", "program:일반경영안정자금", "good_landlord", "일반경영안정자금 착한 임대인"), ("86902", "allow", None, "유사의료업"),
              ("47993", "conditional", "registered_mlm", "등록 다단계판매업"), ("9612", "conditional", "blind_massage", "시각장애인 운영 안마원·안마시술소")]

ttl = [P, "sa:Business a rdfs:Class . sa:Industry a rdfs:Class . sa:Notice a rdfs:Class . sa:Condition a rdfs:Class . sa:Evidence a rdfs:Class . sa:SizeRule a rdfs:Class . sa:ExclusionEntry a rdfs:Class . sa:ExclusionException a rdfs:Class .\n"]
for s, (a, b) in SECTIONS.items():
    ttl.append(f'sa:ind_{s} a sa:Industry ; sa:code "{s}" .')
    for n in range(a, b + 1):
        ttl.append(f'sa:ind_{n:02d} a sa:Industry ; sa:code "{n:02d}" ; sa:broader sa:ind_{s} .')
for key, (name, table) in SOURCES.items():
    ttl.append(f'sa:src_{key} a sa:Source ; rdfs:label "{name}" .')
    for code, v in table.items():
        ttl.append(f'sa:size_{key}_{code} a sa:SizeRule ; sa:source sa:src_{key} ; sa:code "{code}" ; sa:maxRevenue {int(v * 10**8)} .')
for i, (code, partial, name) in enumerate(EXCL):
    ttl.append(f'sa:excl_{i} a sa:ExclusionEntry ; sa:list sa:PolicyFundExclusion ; sa:code "{code}" ; sa:partial {"true" if partial else "false"} ; rdfs:label "{name}" .')
for i, (code, kind, field, name) in enumerate(EXCEPTIONS):
    f = f' ; sa:field "{field}"' if field else ""
    ttl.append(f'sa:exc_{i} a sa:ExclusionException ; sa:code "{code}" ; sa:kind "{kind}"{f} ; rdfs:label "{name}" .')
for n in ("1068107", "1068077", "1071565", "1065100"):
    ttl.append(f'sa:notice_{n} a sa:Notice ; sa:usesExclusionList sa:PolicyFundExclusion .')
open(f"{R}/ontology/sosang.ttl", "w").write("\n".join(ttl) + "\n")

SHAPES = P + """@prefix sh: <http://www.w3.org/ns/shacl#> .
sa:ConditionShape a sh:NodeShape ; sh:targetClass sa:Condition ;
  sh:property [ sh:path sa:field ; sh:minCount 1 ; sh:maxCount 1 ; sh:datatype xsd:string ; sh:message "조건에 대상 항목이 없습니다" ] ;
  sh:property [ sh:path sa:op ; sh:minCount 1 ; sh:maxCount 1 ; sh:in ("eq" "ne" "lt" "le" "gt" "ge" "in" "not_in" "between" "derived") ; sh:message "허용되지 않은 연산자입니다" ] ;
  sh:property [ sh:path sa:kind ; sh:minCount 1 ; sh:in ("eligibility" "exclusion" "period") ; sh:message "조건 종류가 잘못됐습니다" ] ;
  sh:property [ sh:path sa:check ; sh:minCount 1 ; sh:in ("profile" "declared" "discretionary" "unsupported" "conflict") ; sh:message "확인 방식이 잘못됐습니다" ] ;
  sh:property [ sh:path sa:supportedBy ; sh:minCount 1 ; sh:class sa:Evidence ; sh:message "근거 없는 조건은 판정에 쓸 수 없습니다" ] .
sa:EvidenceShape a sh:NodeShape ; sh:targetClass sa:Evidence ;
  sh:property [ sh:path sa:quote ; sh:minCount 1 ; sh:minLength 2 ; sh:message "근거 문구가 없습니다" ] ;
  sh:property [ sh:path sa:page ; sh:minCount 1 ; sh:datatype xsd:integer ; sh:message "근거 쪽 번호가 없습니다" ] .
sa:SizeRuleShape a sh:NodeShape ; sh:targetClass sa:SizeRule ;
  sh:property [ sh:path sa:source ; sh:minCount 1 ; sh:message "규모 기준에 출처가 없습니다" ] ;
  sh:property [ sh:path sa:maxRevenue ; sh:minCount 1 ; sh:datatype xsd:integer ] .
"""
open(f"{R}/ontology/shapes.ttl", "w").write(SHAPES)

# 공고별 별표를 표 순서 그대로 비교: 코드 표기("코드 중" 포함)와 전체 코드를 추출한다.
def table_codes(n):
    s = open(f"{R}/data/text/{n}.txt").read()
    i = [m.start() for m in re.finditer(r"표준산업분류\n", s)]
    seg = s[i[0]:i[0] + 7500]
    return sorted(set(re.findall(r"(?m)^(\d{2,5})(?: 중)?$", seg)) | {x for l in re.findall(r"(?m)^(\d{3,5}(?:, ?\d{3,5})+)(?: 중)?$", seg) for x in re.split(r", ?", l)})


base = table_codes("1071565_정책자금변경5")
print("정책자금 코드", len(base))
for n in ("1068107_브랜드점프업", "1068077_생활문화참여", "1065100_경영안정바우처"):
    c = table_codes(n)
    print(n, len(c), "차이", sorted(set(c) ^ set(base)))
print("온톨로지 항목", len(EXCL), "별표와 차이", sorted(set(base) ^ {x[0] for x in EXCL}))
