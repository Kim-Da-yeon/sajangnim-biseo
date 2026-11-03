# 기대효과 실측(LLM 호출 없음): 규칙 대조만 돌려 시간과 걸러진 공고 수를 잰다.
# 임포트 시 API 키를 무효값으로 두어 실수로라도 유료 호출이 나가지 않게 한다.
import os,sys,glob,json,time,statistics as st
os.environ['ANTHROPIC_API_KEY']='invalid-no-call'
sys.path.insert(0,'/home/abcde/sosang_agent/src'); os.chdir('/home/abcde/sosang_agent')
import app as a
from judge import judge
txt={}
for f in glob.glob('data/text/*'):
    if os.path.isfile(f): txt[os.path.basename(f).split('_')[0]]=len(open(f,encoding='utf-8').read())
ids=list(a.NOTICES); print('ids',ids)
def tx(i):
    k=i.split('_')[-1]
    for c in (i,k,'PBLN'+k[-6:]):
        if c in txt: return txt[c]
L=[tx(i) for i in ids]; print('chars',L)
P={'food':dict(main_industry_ksic='10799',employees=4,revenue_3y_avg=300000000,revenue_2025=300000000,founded_date='2020-03-02',business_status='정상',hq_region='보은군',factory_region='보은군',site_region='보은군',applicant_type='기존 기업'),
'rest':dict(main_industry_ksic='56111',employees=3,revenue_3y_avg=400000000,revenue_2025=90000000,founded_date='2021-01-04',business_status='정상',site_region='정읍시',revenue_compare_period='연도',revenue_before=100000000,revenue_latest=80000000),
'shop':dict(main_industry_ksic='47411',employees=3,revenue_3y_avg=500000000,revenue_2025=80000000,founded_date='2019-05-10',business_status='정상',site_region='포항시')}
for as_of in ('2026-11-03',):
  for name,p0 in P.items():
    p=a.fill(dict(p0)); c={}; t0=time.perf_counter(); q=set(); left=0; n=0
    for i,nn in a.NOTICES.items():
        for prog in nn['programs'] or [None]:
            r=judge(nn['conditions'],p,as_of,prog); n+=1
            key='마감' if r['period_status']=='마감' else r['status']; c[key]=c.get(key,0)+1
            if key not in('마감','불일치'): left+=(tx(i) or 0)
    print(as_of,name,'n',n,c,'ms',round((time.perf_counter()-t0)*1000,1),'남은글자',left)
