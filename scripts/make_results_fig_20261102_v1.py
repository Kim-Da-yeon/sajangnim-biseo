"""결과 그림 생성 스크립트.

흐름: 4차 새 공고 결과 JSON 읽기 → 비교군별 공고 상태 일치 건수를 막대로 그림 → results/fig_holdout4.png 저장.
목적: 코드 고정 후 처음 측정한 수치를 보고서에 그대로 싣는다.
결과 해석: 가상 프로필 24사례, AI 초안 라벨 기준이다. 표본이 작아 공고 전반의 정확도로 해석하지 않는다.
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

R = os.path.expanduser("~/sosang_agent")
s = json.load(open(f"{R}/results/holdout4_v1/final_scores.json"))["scores"]
for f in fm.findSystemFonts():
    if "NanumGothic" in f or "Pretendard" in f or "NotoSansCJK" in f or "NotoSansKR" in f:
        fm.fontManager.addfont(f); plt.rcParams["font.family"] = fm.FontProperties(fname=f).get_name(); break
rows = [("F", "풀 시스템"), ("D", "LLM 직접 응답"), ("A", "최종 판단 제거"), ("C", "최종 판단·온톨로지 제거"), ("A1", "조건 판단까지 제거"), ("A0", "진술 대조까지 제거"), ("B", "단일 에이전트")]
fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=200)
ys = list(range(len(rows)))[::-1]
for y, (k, name) in zip(ys, rows):
    v = s[k]["status_match"]
    ax.barh(y, v, height=.56, color="#0066cc" if k == "F" else "#b4b4ba")
    ax.text(v + .4, y, f"{v}건 · 잘못된 일치 {s[k]['false_match']}건", va="center", fontsize=9, color="#1d1d1f")
ax.set_yticks(ys, [n for _, n in rows], fontsize=9.5, color="#1d1d1f")
ax.set_xlim(0, 34); ax.set_xticks([0, 6, 12, 18, 24]); ax.tick_params(axis="x", labelsize=8, colors="#6e6e73", length=0); ax.tick_params(axis="y", length=0)
ax.set_xlabel("공고 상태 일치 건수 (24사례 중)", fontsize=8.5, color="#6e6e73", loc="left")
for k in ("top", "right", "left"): ax.spines[k].set_visible(False)
ax.spines["bottom"].set_color("#d2d2d7"); ax.grid(axis="x", color="#ececf0", lw=.7); ax.set_axisbelow(True)
fig.tight_layout(); fig.savefig(f"{R}/results/fig_holdout4.png"); print("저장")
