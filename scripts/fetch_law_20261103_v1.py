"""법령 원문 수집 스크립트.

흐름: law.go.kr에서 법령별 일련번호를 찾음 → 본문을 받아 조문이 잡히면 data/law에 텍스트로 저장.
목적: 소상공인이 자주 묻는 노무·세금·영업 법을 법령 질문 자료에 더한다. LLM을 호출하지 않는다.
결과 해석: 수집 시점의 현행 원문이다. 받지 못한 법은 건너뛰고 출력에 남긴다.
"""
import json, os, re, subprocess, urllib.parse as up

R = os.path.expanduser("~/sosang_agent")
LAWS = ["근로자퇴직급여보장법", "기간제및단시간근로자보호등에관한법률", "남녀고용평등과일ㆍ가정양립지원에관한법률", "산업재해보상보험법", "고용보험법", "식품위생법", "가맹사업거래의공정화에관한법률", "개인정보보호법", "여신전문금융업법", "옥외광고물등의관리와옥외광고산업진흥에관한법률", "전자상거래등에서의소비자보호에관한법률", "부가가치세법", "중소기업기본법", "표시ㆍ광고의공정화에관한법률"]
UA = "Mozilla/5.0"
done = {}
for k in LAWS:
    for _ in range(3):
        h = subprocess.run(["curl", "-sL", "-m", "30", "-A", UA, "https://www.law.go.kr/%EB%B2%95%EB%A0%B9/" + up.quote(k)], capture_output=True).stdout.decode("utf-8", "ignore")
        s = re.findall(r"lsiSeq=(\d+)", h)
        if s:
            break
    if not s:
        done[k] = "번호 없음"
        continue
    # 본문 요청에는 시행일이 필요하다. 법령 첫 화면에서 읽는다.
    p = subprocess.run(["curl", "-sL", "-m", "30", "-A", UA, f"https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq={s[0]}"], capture_output=True).stdout.decode("utf-8", "ignore")
    e = (re.findall(r"efYd[=:'\" ]+(\d{8})", p) or re.findall(r"efYd=(\d{8})", h) or [""])[0]
    t = subprocess.run(["curl", "-sL", "-m", "60", "-A", UA, "-e", "https://www.law.go.kr/LSW/lsInfoP.do", "-H", "X-Requested-With: XMLHttpRequest", "-H", "Content-Type: application/x-www-form-urlencoded", "-X", "POST", "-d", f"lsiSeq={s[0]}&efYd={e}&chrClsCd=010202&urlMode=lsInfoP&efGubun=Y&viewCls=lsInfoP&ancYnChk=0", "https://www.law.go.kr/LSW/lsInfoR.do"], capture_output=True).stdout.decode("utf-8", "ignore")
    x = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))
    n = len(re.findall(r"제\d+조(?:의\d+)?\([^)]{2,40}\)", x))
    if n >= 5:
        open(f"{R}/data/law/{k.replace('ㆍ', '')}.txt", "w").write(x)
    done[k] = (n, (re.findall(r"\[시행[^\]]*\]", x) or [""])[0])
print(json.dumps(done, ensure_ascii=False, indent=0))
