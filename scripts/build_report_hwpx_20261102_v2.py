"""보고서 초안을 서식2 순서의 HWPX로 만드는 스크립트.

흐름: 초안 md 읽기 → 제목·문단·표·그림으로 변환 → submission/ 에 저장 → 다시 열어 글자 확인.
목적: HWP 서식에 옮겨 넣거나 그대로 열어 고칠 수 있는 파일을 만든다.
결과 해석: 원본 서식의 레이아웃을 복제한 것이 아니다. 항목 순서와 내용만 서식2를 따른다.
"""
import os, re
from PIL import Image
from hwpx import HwpxDocument

R = os.path.expanduser("~/sosang_agent")
lines = open(f"{R}/docs/report_draft_20261102_v2.md").read().split("\n")
end = lines.index("# [서식1] 기입 내용")
lines = lines[:end]
doc = HwpxDocument.new()
H1 = doc.ensure_run_style(bold=True, size=16)
H2 = doc.ensure_run_style(bold=True, size=13)
H3 = doc.ensure_run_style(bold=True, size=11)


def clean(s):
    return s.replace("**", "").replace("`", "")


def picture(rel, mm=150):
    w, h = Image.open(f"{R}/{rel}").size
    doc.add_picture(open(f"{R}/{rel}", "rb").read(), "png", width_mm=mm, height_mm=mm * h / w)


doc.add_paragraph("2026년 하반기 AI 경진대회 학생 부문(대학생·대학원생)")
doc.add_paragraph("AI 활용 결과 보고서", char_pr_id_ref=H1)
i = 0
while i < len(lines):
    s = lines[i].rstrip()
    if s.startswith("# "):
        pass
    elif s.startswith("## "):
        doc.add_paragraph(s[3:], char_pr_id_ref=H2)
    elif s.startswith("### "):
        doc.add_paragraph(s[4:], char_pr_id_ref=H3)
    elif s.startswith("[화면 삽입"):
        for f in ("flow_start", "flow_evidence", "lease", "calendar"):
            picture(f"results/screens/{f}.png")
    elif s.startswith("[그림 삽입"):
        picture("results/fig_holdout3.png", 140)
    elif s.startswith("|"):
        rows = []
        while i < len(lines) and lines[i].startswith("|"):
            cells = [clean(c.strip()) for c in lines[i].strip().strip("|").split("|")]
            if not all(re.fullmatch(r"-+", c) for c in cells):
                rows.append(cells)
            i += 1
        t = doc.add_table(len(rows), len(rows[0]))
        for a, r in enumerate(rows):
            for b, c in enumerate(r):
                t.set_cell_text(a, b, c)
        doc.add_paragraph("")
        continue
    elif s:
        doc.add_paragraph(clean(re.sub(r"^(\s*)- ", lambda m: m.group(1) + "· ", s)))
    i += 1
os.makedirs(f"{R}/submission", exist_ok=True)
out = f"{R}/submission/서식2_AI활용결과보고서_초안.hwpx"
doc.save_to_path(out)
chk = HwpxDocument.open(out).export_text()
print("저장", out, "글자", len(chk), "표 포함 확인", "풀 시스템" in chk, "그림", sum(1 for _ in HwpxDocument.open(out).part_names if "BinData" in _) if hasattr(HwpxDocument.open(out), "part_names") else "")
