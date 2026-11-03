"""공고 목록(manifest) 생성 스크립트.

흐름: 공고별 메타데이터 정의 → 원본 PDF 해시 계산 → data/manifest.json 저장.
목적: 어떤 공고의 어떤 파일로 개발·평가했는지 고정해 평가 재현성과 개발/평가 분리를 보장한다.
결과 해석: sha256이 바뀌면 원본이 달라진 것이므로 정답 라벨을 다시 확인해야 한다.
"""
import glob, hashlib, json, os

ROOT = os.path.expanduser("~/sosang_agent/data")
BASE = "https://www.mss.go.kr/site/smba/ex/bbs/View.do?cbIdx=310&bcIdx={0}&parentSeq={0}"

# split: dev=규칙·프롬프트 조정에 사용, eval=최종 측정 전까지 추출 결과를 보며 조정 금지
# scope: 정답 라벨을 만드는 범위(공고 전체가 아니라 개별 사업체가 신청하는 유형으로 한정)
NOTICES = [
    dict(id="1071619", dir="1071619_클린3차", title="2026년 소공인 클린제조환경조성 사업 3차 모집 공고",
         notice_no="제2026-580호", split="dev", period=["2026-10-06", "2026-10-20"],
         scope="소공인 개별 신청 공통 자격", role="정정 쌍의 원공고"),
    dict(id="1071870", dir="1071870_클린3차연장", title="2026년 소공인 클린제조환경조성 사업 3차 모집 공고(연장)",
         notice_no="제2026-598호", split="dev", period=["2026-10-06", "2026-10-30"],
         scope="신청기간 변경만", role="정정 쌍(실제 마감 변경)", supersedes="1071619"),
    dict(id="1068077", dir="1068077_생활문화참여", title="2026년 소상공인 생활문화 혁신지원 참여 소상공인 모집 공고",
         notice_no="제2026-325호", split="dev", period=["2026-05-18", "2026-06-08"],
         scope="유형① 단독 신청", role="제외 조건·예외 다수"),
    dict(id="1068107", dir="1068107_브랜드점프업", title="2026년 브랜드 소상공인 점프업 소상공인 모집 공고",
         notice_no="제2026-321호", split="eval", period=["2026-05-11", "2026-05-29"],
         scope="소상공인 신청 자격", role="제외 업종을 다른 사업 기준으로 참조"),
    dict(id="1069018", dir="1069018_판로추가", title="2026년 소공인 판로개척지원사업 추가 모집 공고",
         notice_no="제2026-397호", split="eval", period=["2026-06-15", "2026-06-19"],
         scope="소공인 신청 자격", role="업종·분야·신생업체 조건"),
    dict(id="1069002", dir="1069002_스마트추가", title="2026년 소공인 스마트제조지원사업 추가 모집 공고",
         notice_no="제2026-396호", split="eval", period=["2026-06-15", "2026-07-03"],
         scope="개별형", role="매출 OR 조건(직전년도 또는 3개년 평균)"),
    dict(id="1071565", dir="1071565_정책자금변경5", title="2026년 소상공인 정책자금 융자사업 공고(변경 5차)",
         notice_no="제2026-576호", split="eval", period=None,
         scope="일반경영안정자금, 긴급경영안정자금(일시적 경영애로)", role="매출 15% 감소 및 예외 조건",
         supersedes="1070197"),
    dict(id="1064384", dir="1064384_고용보험료", title="2026년 소상공인 고용보험료 지원사업 공고",
         notice_no="제2025-660호", split="dev", period=["2026-01-01", None], period_note="예산 소진 시까지",
         scope="사업주 지원 대상", role="업종별 소상공인 기준 원문, 오늘 기준 시연용"),
    dict(id="1065100", dir="1065100_경영안정바우처", title="소상공인 경영안정 바우처 지원사업 시행 공고",
         notice_no="제2026-37호", split="eval", period=["2026-02-09", "2026-12-18"], period_note="종료일 잠정, 예산 소진 시 조기 마감 가능",
         scope="지원 요건", role="매출 연 환산 계산, 오늘 기준 시연용"),
    dict(id="PBLN127619", dir="PBLN127619_보은군소공인", title="2026년 보은 식품제조 소공인특화지원센터 기업지원 사업 참여기업 추가 모집공고",
         notice_no="제2026-00호(원문 표기)", split="eval", period=["2026-10-22", "2026-11-05"],
         scope="신청 자격", role="지자체 연계 공고, 일정 표기 불일치 포함, 오늘 기준 시연용",
         url="https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000127619"),
    dict(id="1067425", dir="1067425_재도전추경", title="2026년 재도전성공패키지(추경) 모집공고",
         notice_no="원문 확인", split="eval", period=["2026-04-17", "2026-05-07"],
         scope="예비재창업자, 재창업기업 신청 자격", role="폐업 이력·재창업 업력 조건"),
    dict(id="1070197", dir="1070197_정책자금변경4", title="2026년 소상공인 정책자금 융자사업 공고(변경 4차)",
         notice_no="제2026-478호", split="eval", period=None,
         scope="변경 범위 비교 전용", role="정정 쌍(자격 조건 변경 없음)"),
]
EXCLUDED = [
    dict(id="1069948", title="2026년 소상공인 협업활성화 공동사업 2차 공고", reason="협동조합·연합회 대상이라 개별 사업체 프로필과 맞지 않음"),
    dict(id="1069787", title="2026년 백년소상공인 모집(재지정) 공고", reason="기존 지정 업체 재지정 성격이 강해 일반 사업체 판정 사례를 만들기 어려움"),
]

for n in NOTICES:
    # 스마트 공고의 별첨은 본 공고와 분리해 해시를 남긴다.
    # 보은군 공고처럼 PDF가 없으면 HWPX를 원본으로 기록한다(쪽 번호 없음, 근거는 page=1로 통일).
    pdfs = sorted(glob.glob(f"{ROOT}/raw/{n['dir']}/*.pdf")) or sorted(glob.glob(f"{ROOT}/raw/{n['dir']}/*.hwpx"))
    n.setdefault("url", BASE.format(n["id"]))
    n["files"] = [dict(path=os.path.relpath(p, ROOT), sha256=hashlib.sha256(open(p, "rb").read()).hexdigest()) for p in pdfs]
    n["text"] = f"text/{n['dir']}.txt"

json.dump(dict(collected_on="2026-11-02", source="중소벤처기업부 사업공고 게시판, 기업마당", notices=NOTICES, excluded=EXCLUDED),
          open(f"{ROOT}/manifest.json", "w"), ensure_ascii=False, indent=1)
print("공고", len(NOTICES), "dev", sum(n["split"] == "dev" for n in NOTICES), "eval", sum(n["split"] == "eval" for n in NOTICES))
