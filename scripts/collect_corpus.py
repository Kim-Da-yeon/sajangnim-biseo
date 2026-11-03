"""서비스 공고 코퍼스 수집 스크립트.

흐름: 중기부 사업공고 + 기업마당 목록 조회 → 제목으로 소상공인 혜택 공고 선별 → 첨부 내려받기 → 텍스트 추출 → 목록 저장.
목적: 정답 라벨 평가셋(manifest.json)과 별개로, 서비스가 안내할 공고 범위를 넓힌다.
결과 해석: 제목 기준 1차 선별이므로 실제 소상공인 대상 여부는 본문 확인이 필요하다. 라벨이 없어 정확도 점수에 쓰지 않는다.
"""
import html, json, os, re, subprocess, time, zipfile

ROOT = os.path.expanduser("~/sosang_agent/data/corpus")
UA = "Mozilla/5.0"
# 포함: 소상공인·자영업자·창업자가 직접 받는 혜택 / 제외: 기관 모집, 포상, 공모전 등 사업체 혜택이 아닌 공고
INCLUDE = re.compile("소상공인|소공인|자영업|재도전|재창업|희망리턴|폐업|예비창업패키지|초기창업패키지|창업도약패키지|로컬창업|비즈플러스|바우처|크레딧|배달|고용보험료")
EXCLUDE = re.compile("운영기관|주관기관|수행기관|운영사|포상|공모전|유공|센터 구축|설치 지역|사내벤처|창업보육|복합지원센터|타운|수행 ?기관|딥테크|대회")


def get(url, *args):
    return subprocess.run(["curl", "-sL", "-m", "30", "-A", UA, *args, url], capture_output=True, text=True, errors="ignore").stdout


def mss_rows(pages=30):
    # 중기부 게시판은 쪽당 10건이며, 30쪽이면 대략 2026년 공고 전체가 들어온다.
    rows = []
    for pg in range(1, pages + 1):
        s = get(f"https://www.mss.go.kr/site/smba/ex/bbs/List.do?cbIdx=310&pageIndex={pg}")
        for m in re.finditer(r"<tr[^>]*doBbsFView\('310','(\d+)'[^>]*title=\"([^\"]*)\"(.*?)</tr>", s, re.S):
            x = re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", m.group(3)))
            reg = re.findall(r"20\d\d\.\d\d\.\d\d", x)
            per = re.findall(r"20\d\d-\d\d-\d\d", x)[:2]
            rows.append(dict(source="mss", id=m.group(1), title=html.unescape(m.group(2)), registered=(reg or [None])[0], period=per))
        time.sleep(0.3)
    return rows


def biz_rows(pages=20):
    # 기업마당 목록은 쪽당 15건. 최근 공고만 본다(오늘 기준 접수 가능성이 높은 범위).
    rows = []
    for pg in range(1, pages + 1):
        s = get(f"https://www.bizinfo.go.kr/sii/siia/selectSIIA200View.do?rows=15&cpage={pg}")
        for i, t in re.findall(r"pblancId=([A-Za-z0-9_]+)[^>]*>\s*(.*?)</a>", s, re.S):
            rows.append(dict(source="bizinfo", id=i, title=re.sub(r"\s+", " ", html.unescape(re.sub("<[^>]+>", "", t))).strip(), registered=None, period=[]))
        time.sleep(0.3)
    return rows


def to_text(path):
    # PDF는 쪽 번호를 유지하고, HWPX는 쪽 정보가 없어 전체를 [[p1]]로 둔다.
    if path.endswith(".pdf"):
        import fitz
        return "\n".join(f"[[p{i+1}]]\n" + p.get_text() for i, p in enumerate(fitz.open(path)))
    z, out = zipfile.ZipFile(path), []
    for n in sorted(x for x in z.namelist() if re.match(r"Contents/section\d+\.xml", x)):
        for p in re.findall(r"<hp:p[ >].*?</hp:p>", z.read(n).decode("utf8", "ignore"), re.S):
            t = html.unescape(re.sub("<[^>]+>", "", "".join(re.findall(r"<hp:t[^>]*>(.*?)</hp:t>", p, re.S)))).strip()
            if t:
                out.append(t)
    return "[[p1]]\n" + "\n".join(out)


def download(row):
    # 첨부 형식을 파일 앞부분으로 판별하고, PDF가 있으면 PDF를 본문 원본으로 쓴다.
    if row["source"] == "mss":
        base, page = "https://www.mss.go.kr", f"https://www.mss.go.kr/site/smba/ex/bbs/View.do?cbIdx=310&bcIdx={row['id']}&parentSeq={row['id']}"
        pat = r'href="([^"]*Download\.do[^"]*)"'
    else:
        base, page = "https://www.bizinfo.go.kr", f"https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId={row['id']}"
        pat = r'["\'](/?[^"\' ]*fileDown\.do\?[^"\' ]+)["\']'
    row["url"] = page
    d = f"{ROOT}/raw/{row['source']}_{row['id']}"
    os.makedirs(d, exist_ok=True)
    links = list(dict.fromkeys(html.unescape(x) for x in re.findall(pat, get(page))))
    files = []
    for k, l in enumerate(links[:6]):
        b = f"{d}/f{k}.bin"
        subprocess.run(["curl", "-sL", "-m", "60", "-A", UA, "-e", page, "-o", b, base + ("" if l.startswith("/") else "/") + l])
        head = open(b, "rb").read(8)
        ext = ".pdf" if head.startswith(b"%PDF") else ".hwpx" if head.startswith(b"PK") else ".hwp" if head.startswith(b"\xd0\xcf") else ".bin"
        os.rename(b, f"{d}/f{k}{ext}")
        files.append(f"{d}/f{k}{ext}")
        time.sleep(0.2)
    main = next((f for f in files if f.endswith(".pdf")), None) or next((f for f in files if f.endswith(".hwpx")), None)
    row["n_files"], row["text"] = len(files), None
    if main:
        try:
            s = to_text(main)
            os.makedirs(f"{ROOT}/text", exist_ok=True)
            row["text"] = f"text/{row['source']}_{row['id']}.txt"
            row["chars"] = len(s)
            open(f"{ROOT}/{row['text']}", "w").write(s)
        except Exception as e:
            row["error"] = str(e)[:80]
    else:
        row["error"] = "본문 파일 없음(hwp 전용 또는 첨부 없음)"


os.makedirs(ROOT, exist_ok=True)
rows = mss_rows() + biz_rows()
sel = [r for r in rows if INCLUDE.search(r["title"]) and not EXCLUDE.search(r["title"]) and (r["registered"] is None or r["registered"] >= "2026")]
print("조회", len(rows), "선별", len(sel))
for r in sel:
    download(r)
    print(r["source"], r["id"], r["title"][:52], r["period"], r.get("chars"), r.get("error", ""))
json.dump(sel, open(f"{ROOT}/corpus.json", "w"), ensure_ascii=False, indent=1)
