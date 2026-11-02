// 시연 영상 녹화: 실제 서버에 접속해 화면을 조작한다. 자막과 커서는 녹화 때만 페이지에 넣으며 서비스 코드에는 없다.
// 사용법: node record_demo_20261102_v2.js <저장폴더> (playwright-core 필요)
const {chromium}=require('playwright-core');(async()=>{
const b=await chromium.launch({executablePath:process.env.HOME+'/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome',args:['--no-sandbox']});
const ctx=await b.newContext({viewport:{width:1280,height:800},colorScheme:'light',locale:'ko-KR',recordVideo:{dir:process.argv[2],size:{width:1280,height:800}}});
const p=await ctx.newPage();p.setDefaultTimeout(200000);
const hud=()=>p.evaluate(()=>{const s=document.createElement('style');s.textContent='#cap{position:fixed;left:50%;bottom:26px;transform:translateX(-50%);background:rgba(29,29,31,.92);color:#fff;font:600 19px/1.4 "Pretendard Variable",sans-serif;padding:11px 20px;border-radius:12px;z-index:99;max-width:1060px;text-align:center}#cur{position:fixed;width:20px;height:20px;border-radius:50%;background:rgba(0,102,204,.4);border:2px solid #0066cc;z-index:98;pointer-events:none;transition:left .55s cubic-bezier(.23,1,.32,1),top .55s cubic-bezier(.23,1,.32,1);left:640px;top:400px}';document.head.append(s);const c=document.createElement('div');c.id='cap';document.body.append(c);const u=document.createElement('div');u.id='cur';document.body.append(u)});
const cap=(t,ms=4200)=>p.evaluate(t=>document.getElementById('cap').textContent=t,t).then(()=>p.waitForTimeout(ms));
const point=async(el)=>{await el.scrollIntoViewIfNeeded();const r=await el.boundingBox();await p.evaluate(([x,y])=>{const u=document.getElementById('cur');u.style.left=x+'px';u.style.top=y+'px'},[r.x+r.width/2-10,r.y+r.height/2-10]);await p.waitForTimeout(600)};
const click=async(el)=>{await point(el);await el.click()};const idle=()=>p.waitForFunction(()=>!document.getElementById('go').disabled,null,{timeout:200000});
const tab=async v=>{await click(await p.$(`#tabs button[data-v=${v}]`));await p.waitForTimeout(500)};
await p.goto('http://127.0.0.1:8000/');await hud();
await cap('사장님 행정비서 (가상 데이터로 시연)',4500);
await click(await p.$('#preset button[data-p=shop]'));await p.waitForSelector('.row');await idle();await p.waitForTimeout(800);
await cap('가게 정보를 넣으면 공고를 일치, 확인 필요, 불일치로 나눕니다');
const qs=await p.$$eval('#common .q',e=>e.map(x=>x.querySelector('.qt').textContent));const i=qs.findIndex(s=>/주류|담배|술/.test(s));const row=(await p.$$('#common .q'))[i];await point(row);
await cap('모르는 조건은 질문으로 묻습니다. 답은 모든 공고에 반영됩니다');
await click((await row.$$('.yn button'))[0]);await idle();await p.waitForTimeout(800);
const ok=await p.$('#list .row');await ok.scrollIntoViewIfNeeded();await p.evaluate(()=>scrollBy(0,-90));await p.waitForTimeout(300);
await cap('답 하나로 포항 공고가 일치로 바뀝니다. 일치는 AI가 공고 전체로 다시 확인합니다',5000);
await click(ok);await p.waitForTimeout(600);await cap('펼치면 조건별 결과와 공고 원문이 나옵니다');
await click(await p.$('.drawer.on .act.main'));await p.waitForSelector('.guide');await p.evaluate(()=>{const g=document.querySelector('.guide');g.scrollIntoView();scrollBy(0,-120)});await cap('할 일을 짧게 정리합니다');
await p.evaluate(()=>scrollTo({top:0,behavior:'smooth'}));await p.waitForTimeout(700);
const bf=await p.textContent('#tally');await p.fill('#revenue_before','100000000');await p.fill('#revenue_latest','80000000');await click(await p.$('#go'));await idle();await p.waitForTimeout(600);await cap('매출이 바뀌면 값만 고쳐 다시 대조합니다');console.log('rev',bf,'=>',await p.textContent('#tally'));
await click(await p.$('#aiGo'));await idle();await p.waitForTimeout(800);await p.evaluate(()=>document.querySelector('#list').scrollIntoView());await p.evaluate(()=>scrollBy(0,-90));await cap('AI 최종 확인: 공고 전체를 읽고 결과와 이유, 물어볼 내용을 정리합니다',5000);console.log('ai',await p.textContent('#tally'));
await tab('lease');await click(await p.$('text=가상 계약서 넣기'));await p.waitForTimeout(600);await click(await p.$('#leaseGo'));await p.waitForSelector('#leaseOut .art');await p.waitForTimeout(400);await p.evaluate(()=>document.querySelector('#leaseOut').scrollIntoView());await p.evaluate(()=>scrollBy(0,-70));
await cap('계약서 날짜로 법에 정한 기간을 계산합니다. 권리 유무는 판단하지 않습니다',5500);
await tab('law');await p.waitForSelector('#lawChanges .art');await cap('바뀐 법령을 원문과 함께 보여줍니다');
const q=await p.$('#lawQ');await point(q);await q.fill('임대료 인상 상한이 몇 퍼센트인가요?');await click(await p.$('#lawGo'));await p.waitForSelector('#lawOut .ans');await p.evaluate(()=>document.querySelector('#lawOut').scrollIntoView());await p.evaluate(()=>scrollBy(0,-120));await cap('조문을 찾아 짧게 답합니다. 내 경우의 판단은 하지 않습니다',5000);
await tab('cal');await cap('마감일을 한 달력에 모으고 7일 안의 일을 먼저 알려 줍니다',5500);
await ctx.close();console.log(await p.video().path());await b.close()})();
