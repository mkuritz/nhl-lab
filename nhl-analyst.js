/* Sports Analyst (NHL) - shared by Bet Lab NHL tab and NHL Lab. Real data only: NHL Lab public data + Book A lines. */
(function(){
const AB={NJ:'NJD',SJ:'SJS',TB:'TBL',LA:'LAK',UTAH:'UTA'};
const E=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const pc=x=>x==null?'–':Math.round(x*100)+'%',f=(x,n=2)=>x==null?'–':(+x).toFixed(n),sv=x=>x==null?'–':(+x).toFixed(3).replace(/^0/,'');
const fmtD=d=>new Date(d+'T12:00').toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric'});
const cache={};
async function J(u){if(!cache[u]){cache[u]=fetch(u).then(r=>r.ok?r.json():null).catch(()=>null)}return cache[u]}
async function odds(days){const m={};for(const d of days){const j=await J('https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates='+d.replace(/-/g,''));(j?.events||[]).forEach(e=>{const c=e.competitions[0],o=(c.odds||[])[0];const ab=x=>AB[x.team.abbreviation]||x.team.abbreviation;const h=c.competitors.find(x=>x.homeAway==='home'),a=c.competitors.find(x=>x.homeAway==='away');if(h&&a)m[ab(a)+'@'+ab(h)]={det:o?.details,ou:o?.overUnder,src:'Book A',st:c.status?.type?.state}})}return m}
function rank(T,key,asc){const s=Object.entries(T).filter(([k,t])=>t.cur&&t.cur.gp).sort((x,y)=>asc?x[1].cur[key]-y[1].cur[key]:y[1].cur[key]-x[1].cur[key]);const r={};s.forEach(([k],i)=>r[k]=i+1);return r}
async function render(el,opt){opt=opt||{};const base=opt.base||'https://nhllab.sportslabshq.com/data/';const plink=opt.plink||((id,n)=>`<a class="nhl-pl-link" data-pid="${E(id)}" href="https://nhllab.sportslabshq.com/#player/${encodeURIComponent(id)}" target="_blank" rel="noopener">${E(n)}</a>`);
el.innerHTML='<div class="card empty" style="padding:16px">Loading NHL Sports Analyst…</div>';
const v='?v='+Math.floor(Date.now()/3e5);const [meta,T,G0,P,S,H]=await Promise.all(['meta','teams','games','players','slate','h2h_flags'].map(k=>J(base+k+'.json'+v)));
if(!T||!G0||!P||!S){el.innerHTML='<div class="card empty" style="padding:16px">NHL analyst data is unavailable right now.</div>';return}
const today=new Date().toLocaleDateString('en-CA',{timeZone:'America/New_York'});
const G=G0.filter(g=>g.state==='FUT'&&g.date>=today).sort((a,b)=>a.date<b.date?-1:a.date>b.date?1:0);const days=[...new Set(G.map(g=>g.date))].slice(0,2);
const O=await odds(days);const GG=G.filter(g=>days.includes(g.date)).filter(g=>{const o=O[g.away+'@'+g.home];return !o||!o.st||o.st==='pre'});
const N=Object.keys(T).length,off=rank(T,'gfpg'),def=rank(T,'gapg',true),pp=rank(T,'pp'),pk=rank(T,'pk');
const gl=(gid,t)=>(S.goalies||[]).find(x=>x.gid===gid&&x.team===t);
const injOf=t=>P.filter(p=>p.team===t&&p.inj&&!/day-to-day/i.test(p.inj.status)&&((p.prev&&p.prev.p>=30)||(p.cur&&p.cur.p>=5)||p.pos==='G'));
const rec=t=>{const x=T[t];return E(`${x.w}-${x.l}-${x.otl}${x.streak?' · '+x.streak:''}`)};
const bundles=[];
const cards=GG.map(g=>{const a=g.away,h=g.home,A=T[a],Hh=T[h];if(!A||!Hh)return '';const s=[];const o=O[a+'@'+h];
s.push(`<b>${E(a)}</b> ${rec(a)} (${E(A.road)} road) vs <b>${E(h)}</b> ${rec(h)} (${E(Hh.home)} home)`);
if(o&&o.det)s.push(`Market: <b>${E(o.det)}</b>, total ${E(o.ou)} <span class="mut" style="font-size:11px">(${E(o.src)})</span>`);
const ga=gl(g.id,a),gh=gl(g.id,h);
const gs=x=>{if(!x||!x.goalie)return'–';const nm=x.gid_?plink(x.gid_,x.goalie):E(x.goalie);const wk=x.weak_goalie||((x.sv!=null&&x.sv<=0.892)&&((x.l10_sv!=null&&x.l10_sv<=0.888)||(x.l10_gsax!=null&&x.l10_gsax<=-1.8)));return `${nm} ${sv(x.l10_sv??x.sv)}${wk?` <b style="color:#f87171">weak crease${x.l10_gsax!=null?' ('+(x.l10_gsax>0?'+':'')+f(x.l10_gsax,1)+' GSAx)':''}</b>`:''}`};
if(ga||gh)s.push(`Goalies: ${gs(ga)} vs ${gs(gh)} <span class="mut" style="font-size:11px">(${E((ga||gh).status||'Projected')})</span>`);
[[a,h],[h,a]].forEach(([x,y])=>{if(off[x]<=5&&def[y]>=N-4){s.push(`<b style="color:#4ade80">Mismatch:</b> ${E(x)} offense #${off[x]} (${f(T[x].cur.gfpg)} GF/gm) vs ${E(y)} defense #${def[y]} of ${N} (${f(T[y].cur.gapg)} GA/gm)`);
const tp=S.rows.filter(r=>r.gid===g.id&&r.team===x).sort((p,q)=>q.pP-p.pP).slice(0,2);if(tp.length===2)bundles.push({g,x,y,tp,pr:tp[0].pP*tp[1].pP})}
if(pp[x]<=8&&pk[y]>=N-7)s.push(`<b style="color:#4ade80">Special teams edge:</b> ${E(x)} PP ${pc(T[x].cur.pp)} (#${pp[x]}) vs ${E(y)} PK ${pc(T[y].cur.pk)} (#${pk[y]})`)});
const expRows=S.rows.filter(r=>r.gid===g.id&&r.exploit_tags&&r.exploit_tags.length).sort((p,q)=>(q.pGm??q.pG)-(p.pGm??p.pG));
if(expRows.length)s.push(`<b style="color:#38bdf8">Weakness exploit:</b> ${plink(expRows[0].pid,expRows[0].name)} (${E(expRows[0].team)}) · ${E(expRows[0].exploit_tags.join(' · '))}`);
if(g.aB2B||g.hB2B)s.push(`<b style="color:#fbbf24">Back-to-back:</b> ${E([g.aB2B?a:null,g.hB2B?h:null].filter(Boolean).join(' and '))} played the day before`);
else if(g.aRest!=null&&g.hRest!=null&&Math.abs(g.aRest-g.hRest)>=2)s.push(`Rest: ${E(a)} ${E(g.aRest)} day(s), ${E(h)} ${E(g.hRest)} day(s)`);
const inj=[...injOf(a),...injOf(h)];if(inj.length)s.push(`<b style="color:#f87171">Out/IR:</b> ${inj.slice(0,5).map(p=>`${plink(p.id,p.name)} (${E(p.team)}, ${E(p.inj.status)})`).join(', ')}`);
const top=S.rows.filter(r=>r.gid===g.id).sort((p,q)=>q.pP-p.pP)[0];if(top)s.push(`Top model highlight: ${plink(top.pid,top.name)} (${E(top.team)}) ${pc(top.pP)} to record a point${top.why&&top.why[0]?' · '+E(top.why[0]):''}`);
const hf=(H||[]).filter(x=>(x.team===a&&x.opp===h)||(x.team===h&&x.opp===a)).sort((p,q)=>p.pv-q.pv)[0];if(hf)s.push(`H2H: ${plink(hf.pid,hf.name)} ${E(hf.label)}`);
return `<div class="card" style="padding:12px 14px"><div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap"><b style="font-size:15px">${E(a)} @ ${E(h)}</b><span class="mut" style="font-size:12px">${fmtD(g.date)} ${E(g.time||'')} ET</span></div><div class="mut" style="font-size:12px">${E(g.venue||'')}</div><ul style="margin:6px 0 0 18px;padding:0;line-height:1.5;font-size:13px">${s.map(x=>`<li>${x}</li>`).join('')}</ul></div>`}).join('');
const fair=p=>p>=.5?'-'+Math.round(100*p/(1-p)):'+'+Math.round(100*(1-p)/p);
const bh=bundles.length?`<div class="card" style="padding:12px 14px;margin-bottom:12px"><b>🎯 Advantage bundles: top-5 offense vs bottom-5 defense</b>${bundles.map(b=>`<div style="padding:6px 0;border-bottom:1px solid rgba(148,163,184,.2);font-size:13px"><b>${E(b.x)}</b> vs ${E(b.y)} (${fmtD(b.g.date)}): ${b.tp.map(t=>`${plink(t.pid,t.name)} 1+ pt (${pc(t.pP)})`).join(' + ')} · ${pc(b.pr)} if independent, fair ${fair(b.pr)}</div>`).join('')}<div class="mut" style="font-size:11px;margin-top:6px">Same-team legs are positively correlated, so the true joint chance runs a bit higher. Estimates, not betting advice.</div></div>`:`<div class="mut" style="font-size:12px;margin-bottom:10px">No strict top-5 offense vs bottom-5 defense pairing on this slate.</div>`;
el.innerHTML=`<div style="padding:0 ${opt.pad??20}px 20px"><div class="kick">NHL · Sports Analyst desk</div><h2 style="margin:4px 0">🎙️ Game storylines & advantage spots</h2><div class="mut" style="font-size:12px;margin-bottom:10px">Each game: records, the Book A line, projected goalies, offense/defense and special-teams mismatches, rest, injuries, the model's top highlight and the strongest head-to-head flag. Ranks use this season's per-game rates. Stats: Sports Labs model (official stats + injury report), data ${E(meta?.updatedET||'')}; lines from public market data. Early-season samples are small.</div>${bh}<div style="display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(min(340px,100%),1fr))">${cards||'<div class="mut">No upcoming NHL games in the data window.</div>'}</div></div>`}
window.NHLAnalyst=render;
})();
