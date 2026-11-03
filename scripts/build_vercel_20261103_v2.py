"""Vercel 배포 폴더 생성 스크립트.

흐름: 실행에 필요한 코드·조건·공고 원문만 deploy_vercel/에 복사 → 진입 파일과 설정 작성.
목적: API 키와 원본 파일, 평가 자료를 빼고 무료 플랜에서 돌아가는 최소 묶음을 만든다.
결과 해석: 공고 원문은 서버 안에서 조건 판단에만 쓰며 주소로 내려받을 수 없다. 이 폴더는 저장소에 올리지 않는다.
"""
import glob, json, os, re, shutil

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = f"{R}/deploy_vercel"
if os.path.exists(D):
    shutil.rmtree(D)  # 이 스크립트가 만드는 산출물 폴더만 지운다


def put(rel, dest=None):
    dest = f"{D}/{dest or rel}"
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy(f"{R}/{rel}", dest)


for f in ("src/judge_20261103_v7.py", "src/agents_20261103_v13.py", "src/assistant_20261103_v6.py", "src/app_20261103_v10.py", "web/index.html", "ontology/sosang.ttl", "ontology/shapes.ttl", "ontology/law.ttl", "data/prepared_money.json", "data/law/law_items.json", "data/samples/lease_sample_virtual.txt", "data/manifest.json", "results/question_cache.json"):
    put(f)
for f in glob.glob(f"{R}/data/prepared/*.json") + glob.glob(f"{R}/results/eval_v2_posthoc/extract_*.json") + glob.glob(f"{R}/data/labels/eval_[0-9P]*.json"):
    put(os.path.relpath(f, R))
ids = [os.path.basename(f)[:-5] for f in glob.glob(f"{R}/data/prepared/*.json")]
n = 0
for i in ids:
    p = f"data/corpus/text/{i}.txt"
    if os.path.exists(f"{R}/{p}"):
        put(p); n += 1
for f in glob.glob(f"{R}/data/labels/eval_[0-9P]*.json"):
    p = f"data/text/{json.load(open(f))['source_text']}.txt"
    if os.path.exists(f"{R}/{p}"):
        put(p); n += 1
os.makedirs(f"{D}/api", exist_ok=True)
open(f"{D}/api/index.py", "w").write("""import os, sys
from urllib.parse import parse_qs, urlencode
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from app_20261103_v10 import app  # noqa: E402


class RestorePath:
    # Vercel 재작성 뒤에도 앱이 원래 주소를 보도록, vercel.json이 넘긴 __path로 주소를 되돌린다.
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            q = parse_qs(scope.get("query_string", b"").decode(), keep_blank_values=True)
            if "__path" in q:
                p = "/" + q.pop("__path")[0].lstrip("/")
                scope = dict(scope, path=p, raw_path=p.encode(), query_string=urlencode(q, doseq=True).encode())
        await self.inner(scope, receive, send)


app.add_middleware(RestorePath)
""")
open(f"{D}/requirements.txt", "w").write("anthropic==2.3.0\nfastapi==0.162.0\nuvicorn==0.54.0\nrdflib==7.6.0\nPyMuPDF\n")
json.dump({"regions": ["icn1"], "rewrites": [{"source": "/(.*)", "destination": "/api/index?__path=/$1"}], "functions": {"api/index.py": {"includeFiles": "{src,web,ontology,data,results}/**", "maxDuration": 300}}}, open(f"{D}/vercel.json", "w"), indent=1)
print("공고 원문", n, "건")
