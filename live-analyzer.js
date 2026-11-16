/* NHL Lab: Live Analyzer (beta, uncalibrated). Intermission player ratings + live-bet board from official play-by-play and shift data.
   Data: data/live/index.json + <gid>_<stage>.json (written by the private engine). No live prices. Uncalibrated. */
(function(){
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const mm=s=>{s=Math.round(s||0);return Math.floor(s/60)+':'+String(s%60).padStart(2,'0')};
const pc=v=>v==null?'–':(v*100).toFixed(v<0.1?1:0)+'%';
const am=n=>n==null?'–':Math.abs(n)>3000?'>+3000':(n>0?'+':'')+n;
const SN={p1:'End of 1st',p2:'End of 2nd',reg:'End of 3rd',final:'Final'};
const FL={trend:['📈','Trending'],due:['🎯','Volume, no payoff'],involved:['🔥','Involved'],cool:['🧊','Cool / fade'],absent:['⚠️','No ice time this period']};
const CN={off:'Offense',use:'Usage',inv:'Involvement',poss:'Possession proxy',mis:'Mistakes'};
const cache={};
let BASE='data/live/';
async function J(u){const r=await fetch(BASE+u+'?t='+Math.floor(Date.now()/20000));if(!r.ok)throw new Error(r.status);return r.json()}
const q=new URLSearchParams(location.search);if(q.get('lasrc'))BASE=q.get('lasrc').replace(/\/?$/,'/');
const etToday=()=>new Date().toLocaleDateString('en-CA',{timeZone:'America/New_York'});
const fmtDay=d=>new Date(d+'T12:00').toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric'});
const shiftDate=(d,n)=>{const x=new Date(d+'T12:00');x.setDate(x.getDate()+n);const y=x.getFullYear(),m=String(x.getMonth()+1).padStart(2,'0'),day=String(x.getDate()).padStart(2,'0');return y+'-'+m+'-'+day};
const relLabel=(d,td)=>{const x=(new Date(d+'T12:00')-new Date(td+'T12:00'))/864e5;return x===-1?'Yesterday':x===0?'Today':x===1?'Tomorrow':fmtDay(d)};
const latestStage=G=>{const order=['p1','p2','reg','final'];let s=null;for(const k of order) if(G&&G.stages&&G.stages[k]) s=k;return s};
const CSS=`<style id="lacss">
.la-games{display:flex;gap:6px;overflow-x:auto;padding:2px 0 8px;margin-bottom:10px;scrollbar-width:thin;-webkit-overflow-scrolling:touch}.la-games a{flex:0 0 auto;display:inline-flex;align-items:center;gap:5px;padding:5px 11px;border-radius:99px;background:var(--p);border:1px solid var(--b);color:var(--m);font-size:12px;font-weight:700;white-space:nowrap;cursor:pointer}.la-games a.on{background:var(--a);color:#000;border-color:var(--a)}
.la-dates{display:flex;gap:6px;align-items:center;overflow-x:auto;padding:2px 0 8px;margin-bottom:2px;scrollbar-width:thin;-webkit-overflow-scrolling:touch}.la-dates a{flex:0 0 auto;display:inline-flex;flex-direction:column;align-items:center;gap:1px;padding:5px 12px;border-radius:99px;background:var(--p);border:1px solid var(--b);color:var(--m);font-size:12px;font-weight:700;white-space:nowrap;cursor:pointer;line-height:1.15}.la-dates a.on{background:var(--a);color:#000;border-color:var(--a)}.la-dates a .la-dsub{font-size:10px;font-weight:600;opacity:.75}.la-dates a.on .la-dsub{opacity:.85}.la-dates a.la-arr{flex-direction:row;padding:7px 11px;font-size:16px;line-height:1}.la-dates a.off{opacity:.35;pointer-events:none;cursor:default}
.la-top{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:10px}.la-prev{background:#2a2205;border:1px solid #6b5512;color:var(--y);font-size:11px;font-weight:800;border-radius:99px;padding:3px 10px;letter-spacing:.04em}
.la-stage{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 12px}.la-stage a{padding:6px 14px;border-radius:99px;background:var(--p);border:1px solid var(--b);color:var(--m);font-weight:700;font-size:13px}.la-stage a.on{background:var(--a);color:#000;border-color:var(--a)}.la-stage a.off{opacity:.4;pointer-events:none}
.la-score{display:flex;gap:18px;align-items:center;flex-wrap:wrap}.la-score b{font-size:26px;letter-spacing:.5px}.la-score .tm{font-weight:800;font-size:15px}
.la-cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(340px,100%),1fr));gap:14px;margin-bottom:14px}.la-cols>.card{margin:0;min-width:0}
.la-ent{padding:10px 0;border-bottom:1px solid var(--b)}.la-ent:last-child{border:0}.la-ent .h{display:flex;gap:9px;align-items:center}.la-ent img{width:36px;height:36px;border-radius:50%;background:var(--p2);flex:0 0 auto}
.la-ent .n{font-weight:800}.la-ent .rt{margin-left:auto;font-weight:900;font-size:18px;text-align:right;line-height:1}.la-ent .rt small{display:block;font-size:10px;font-weight:600;color:var(--m)}
.la-mk{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:4px;margin-top:6px}.la-mk>div{background:#ffffff0d;border-radius:6px;padding:4px 6px;font-size:11px;color:var(--m);line-height:1.25}.la-mk b{display:block;color:var(--t);font-size:13px}.la-mk .x{opacity:.45}
.la-why{font-size:12px;color:var(--m);margin-top:5px}.la-nx{margin-top:5px;font-size:11.5px;padding:3px 8px;border-radius:6px;background:#10203a;border:1px solid #1f3f6a;color:#b8cdf0;display:inline-block}.la-nx.hit{background:#0c2b20;border-color:#1d6b4c;color:var(--g)}.la-nx.miss{background:#2d121e;border-color:#882642;color:#fda4af}
.la-rt{display:inline-block;min-width:38px;text-align:center;padding:2px 6px;border-radius:6px;font-weight:900}
.la-cb{display:inline-block;width:46px;height:8px;background:#0d1326;border-radius:4px;position:relative;vertical-align:middle;overflow:hidden}.la-cb i{position:absolute;top:0;bottom:0}.la-cb u{position:absolute;left:50%;top:0;bottom:0;width:1px;background:#4b5578}
.la-sh{height:8px;border-radius:4px;background:linear-gradient(90deg,var(--a),var(--v));display:block}
.la-meth li{margin:4px 0}.la-meth ul{padding-left:18px;margin:6px 0}
.la-pill{display:inline-flex;gap:4px;align-items:center;font-size:10.5px;font-weight:800;padding:1.5px 8px;border-radius:99px;border:1px solid var(--b);background:#16203a;color:#c7d7fe;margin:1px 2px 1px 0}
.la-pill.trend{background:#0c2b20;border-color:#1d6b4c;color:var(--g)}.la-pill.due{background:#1c1638;border-color:#4b398f;color:#d2beff}.la-pill.involved{background:#2c2206;border-color:#85640e;color:var(--y)}.la-pill.cool,.la-pill.absent{background:#0f293d;border-color:#1f5882;color:var(--a)}
</style>`;
if(!document.getElementById('lacss'))document.head.insertAdjacentHTML('beforeend',CSS);
const rcol=v=>v>=65?'background:#0f3326;color:#4ade80':v>=55?'background:#12281f;color:#9be7b9':v<=35?'background:#3a1420;color:#ff8da0':v<=45?'background:#2b1420;color:#f0a5b3':'background:var(--p2);color:var(--t)';
const cbar=z=>{const w=Math.min(50,Math.abs(z)/2.5*50);return `<span class="la-cb" title="${z>0?'+':''}${z}"><u></u><i style="${z>=0?`left:50%;width:${w}%;background:var(--g)`:`right:50%;width:${w}%;background:var(--r)`}"></i></span>`};
const plink=(id,n)=>`<a class="nhl-pl-link" data-pid="${id}" href="#player/${id}">${esc(n)}</a>`;

function mkBox(e,grades){
  const L=e.line,g=e.goal,p=e.point,s=e.sog;
  const cell=(lab,done,live,base,fair)=>done?`<div class="x">${lab}<b>done</b>already cashed</div>`:`<div>${lab} (rest of reg.)<b>${pc(live)} <span class="m small">vs ${pc(base)}</span></b>fair ${am(fair)}</div>`;
  const pl=e.pregame_line;
  return `<div class="la-mk">${cell('Goal',g.done,g.live,g.base,g.fair)}${cell('Point',p.done,p.live,p.base,p.fair)}<div>SOG ${s.so_far} so far<b>${pc(s.ge1)} <span class="m small">1+ more</span></b>${pc(s.ge2)} 2+ · exp ${s.live_mean}</div></div>`;
}
function nextTag(e,grades,stage){
  if(!grades)return '';const gi=grades.find(x=>x.gid===e._gid&&x.stage===stage);if(!gi)return '';
  const it=gi.items.find(i=>i.pid===e.pid&&i.sig===e.signal);if(!it)return '';
  const txt=`${it.g}G ${it.p-it.g}A, ${it.sog} SOG`;const cls=it.hit===true?'hit':it.hit===false?'miss':'';
  return `<div class="la-nx ${cls}">${gi.span} actual: ${txt}${it.hit===true?` ✓ ${it.mkt}`:it.hit===false?` ✗ ${it.mkt}`:''}</div>`;
}
function entry(e,D,grades,stage){
  const L=e.line;e._gid=D.gid;
  const line=`${L.g}G ${L.a}A · ${L.sog} SOG (${L.att} att, ${L.hd} HD) · TOI ${mm(L.toi)} (${L.toiRatio>=1?'+':''}${Math.round((L.toiRatio-1)*100)}% vs norm) · last period ice time ${Math.round((L.lastPerRatio||0)*100)}% of norm`;
  const pre=e.pre!=null?`pregame ${pc(e.pre)} full game`:'';
  const pg=e.pregame_line?` · pregame line ${esc(e.pregame_line.book)} ${am(e.pregame_line.price)}`:'';
  return `<div class="la-ent"><div class="h"><img loading="lazy" src="${esc(D._head?.[e.pid]||'')}" alt="" onerror="this.style.visibility='hidden'"><div><span class="n">${plink(e.pid,e.name)}</span> <span class="m small">${esc(e.team)} · ${esc(e.pos)}</span><div class="small m">${line}</div></div><div class="rt"><span class="la-rt" style="${rcol(e.rating)}">${e.rating.toFixed(0)}</span><small>rating</small></div></div>
  ${mkBox(e)}<div class="la-why">${esc(e.why)}</div><div class="small m" style="margin-top:3px">${pre}${pg}</div>${nextTag(e,grades,stage)}</div>`;
}
function boardHTML(D,grades,stage){
  const B=D.board;if(!B)return '';
  const sec=(k,sub)=>`<div class="card"><h3>${FL[k][0]} ${FL[k][1]} <span class="m small" style="font-weight:500">${sub}</span></h3>${B[k].length?B[k].map(e=>entry(e,D,grades,stage)).join(''):'<div class="m small">Nobody meets the bar right now.</div>'}</div>`;
  return `<h3 style="margin:14px 0 8px">Live-bet board for the ${B.for}${stage==='p1'?' <span class="m small">(early read: one period of data, treat lightly)</span>':''}</h3>
  <div class="note" style="margin-bottom:10px">No live prices are used. "Live" is our model's chance for the rest of regulation after updating the pregame probability with what happened so far. "Fair" is the model's price: compare it with the live line you see. Uncalibrated: it has no forward record yet, so size accordingly.</div>
  <div class="la-cols">${sec('trend','shot pace and usage above his norm')}${sec('due','chances created, nothing scored yet')}${sec('involved','playing well across the board')}${sec('cool','scored on little, or ice time dropping')}</div>
  <div class="small m" style="margin:-4px 0 12px">Volume without payoff: shot volume is a real signal, finishing luck is not "owed". The board only moves a probability by how much the extra chances change his rate.</div>`;
}
function otHTML(D){
  const o=D.ot;if(!o)return '';
  const mx=Math.max(...o.scorers.map(x=>x.share));
  return `<h3 style="margin:14px 0 8px">Overtime view <span class="m small">tied ${D.score.away}-${D.score.home} after regulation</span></h3>
  <div class="la-cols"><div class="card"><h3>🏁 Most likely to score in OT</h3><div class="small m" style="margin-bottom:6px">${esc(o.shareNote)}</div><table><thead><tr><th>Player</th><th>Share</th><th></th><th>3v3 att</th><th>3v3 G</th><th>Pregame G%</th><th>Tonight</th></tr></thead><tbody>${o.scorers.map(x=>`<tr><td class="l">${plink(x.pid,x.name)} <span class="m small">${esc(x.team)} ${esc(x.pos)}</span></td><td data-v="${x.share}"><b>${(x.share*100).toFixed(1)}%</b></td><td style="width:90px"><i class="la-sh" style="width:${x.share/mx*100}%"></i></td><td>${x.otAtt}</td><td>${x.otG}</td><td>${pc(x.pG)}</td><td><span class="la-rt" style="${rcol(x.rating)}">${x.rating.toFixed(0)}</span></td></tr>`).join('')}</tbody></table></div>
  <div class="card"><h3>🧊 Best at 3-on-3 (season history)</h3><table><thead><tr><th>Player</th><th>3v3 attempts</th><th>3v3 goals</th></tr></thead><tbody>${o.best3v3.map(x=>`<tr><td class="l">${plink(x.pid,x.name)} <span class="m small">${esc(x.team)}</span></td><td>${x.otAtt}</td><td>${x.otG}</td></tr>`).join('')}</tbody></table><p class="small m">${esc(o.note)}</p></div></div>`;
}
function tableHTML(D,st){
  const rows=D.rows.filter(r=>(st.team==='all'||r.team===st.team)&&(st.role==='all'||r.role===st.role)&&(!st.props||r.props));
  const teams=[D.away,D.home];
  const flt=`<div class="filters"><select data-la="team"><option value="all">Both teams</option>${teams.map(t=>`<option${st.team===t?' selected':''}>${t}</option>`).join('')}</select><select data-la="role">${[['all','Forwards + D'],['F','Forwards'],['D','Defense']].map(([v,l])=>`<option value="${v}"${st.role===v?' selected':''}>${l}</option>`).join('')}</select><label class="small m" style="display:flex;gap:5px;align-items:center"><input type="checkbox" data-la="props"${st.props?' checked':''}> Prop-market players only</label></div>`;
  return `<div class="card"><h3>Player ratings <span class="m small" style="font-weight:500">${rows.length} skaters · 50 = typical for the role · ${D.stage==='final'?'whole game':'through '+SN[D.stage].toLowerCase().replace('end of ','')}</span></h3>${flt}<div class="tw"><table><thead><tr><th>Player</th><th>Team</th><th>Rating</th><th>TOI</th><th>vs norm</th><th>G-A</th><th>SOG</th><th>Att</th><th>HD</th><th>ixG</th><th>H</th><th>B</th><th>TK</th><th>GV</th><th>On-ice 5v5 att%</th>${Object.values(CN).map(c=>`<th class="hide-m">${c}</th>`).join('')}<th class="l">Why</th></tr></thead><tbody>${rows.map(r=>{const L=r.line;return `<tr><td class="l"><img loading="lazy" class="tlogo" style="border-radius:50%;width:22px;height:22px" src="${esc(r.head||'')}" alt="" onerror="this.style.display='none'">${plink(r.pid,r.name)} <span class="m small">${esc(r.pos)}</span>${r.props?' <span class="pill" style="font-size:9px" title="Has prop markets">P</span>':''}${r.flags.map(f=>`<span class="la-pill ${f}" title="${FL[f]?FL[f][1]:f}">${FL[f]?FL[f][0]:''}</span>`).join('')}</td><td>${esc(r.team)}</td><td data-v="${r.rating}"><span class="la-rt" style="${rcol(r.rating)}">${r.rating.toFixed(0)}</span></td><td data-v="${L.toi}">${mm(L.toi)}${L.pp>=30?` <span class="m small">(${mm(L.pp)} PP)</span>`:''}</td><td data-v="${L.toiRatio}" class="${L.toiRatio>=1.1?'g':L.toiRatio<=0.88?'r':''}">${L.toiRatio>=1?'+':''}${Math.round((L.toiRatio-1)*100)}%</td><td data-v="${L.g*10+L.a}">${L.g}-${L.a}</td><td>${L.sog}</td><td>${L.att}</td><td>${L.hd}</td><td data-v="${L.ixg}">${L.ixg.toFixed(2)}</td><td>${L.hits}</td><td>${L.blk}</td><td>${L.tk}</td><td class="${L.gvD>=2?'r':''}" title="${L.gvD} in own zone">${L.gv}</td><td data-v="${L.cf5??-1}">${L.cf5==null?'–':L.cf5+'%'} <span class="m small">(${L.cfOn}-${L.caOn})</span></td>${Object.keys(CN).map(c=>`<td class="hide-m" data-v="${r.comp[c]}">${cbar(r.comp[c])}</td>`).join('')}<td class="l small" style="white-space:normal;min-width:260px">${esc(r.why)}</td></tr>`}).join('')}</tbody></table></div></div>`;
}
const METH=`<div class="card la-meth"><h3>How the rating works</h3><p class="small">Every skater gets a 1-99 rating (50 = typical for his role, forwards and defensemen are scored against their own role). It is built from five parts, all from official play-by-play and shift data cut at the end of the period. Early in a game the rating stays close to 50 because a few minutes of ice time says little. Parts, forward / defense weights:</p><ul class="small"><li><b>Offense (30% / 15%)</b>: shot attempts, shot quality (our own chance model), goals and assists per 60 minutes.</li><li><b>Usage (15% / 20%)</b>: ice time against his own season norm, plus power-play time.</li><li><b>Involvement (10% / 20%)</b>: hits, blocks, takeaways and penalties drawn.</li><li><b>Possession proxy (25% / 25%)</b>: share of 5v5 shot attempts while he is on the ice, and how that compares with his team when he is off. True puck-possession time is not published, so this is a proxy.</li><li><b>Mistakes (20% / 20%)</b>: giveaways (own-zone giveaways count double) and penalty minutes.</li></ul><p class="small m">Live-bet board: trending = shot pace and usage above his norm; volume without payoff = real chances, nothing scored; involved = high rating; cool = scored on little, or ice time dropping. Pregame probabilities from our slate are the baseline and are updated with Bayesian shrinkage. No live odds are pulled. Weights are judgment priors, not fitted, and every board is logged so it can be graded on a forward record. Treat it as a screen, not a signal to stake on.</p></div>`;
window.NHLLive=async function(el,opts){
  const D0=opts&&opts.D;let IDX;
  el.innerHTML='<div class="card m">Loading Live Analyzer…</div>';
  try{IDX=await J('index.json')}catch(e){el.innerHTML=`<h2>⏱️ Live Analyzer</h2><div class="card"><span class="la-prev">BETA · UNCALIBRATED</span><p>No intermission boards yet. Boards appear at the end of the 1st and 2nd period of each game, and after regulation if a game is tied.</p></div>`;return}
  let grades=null;try{grades=await J('board_grades.json')}catch(e){}
  const hasB=g=>g&&g.stages&&Object.keys(g.stages).length>0;
  const allDates=()=>{const td=etToday();const s=new Set([shiftDate(td,-1),td,shiftDate(td,1)]);
    for(const g of Object.values(IDX.games||{})) if(g.date)s.add(g.date);
    if(D0&&Array.isArray(D0.games)) for(const g of D0.games) if(g.date)s.add(g.date);
    return [...s].sort()};
  const gamesOn=date=>{
    const fromIdx=Object.values(IDX.games||{}).filter(g=>g.date===date);
    const have=new Set(fromIdx.map(g=>String(g.gid)));
    const extra=[];
    if(D0&&Array.isArray(D0.games)){
      for(const g of D0.games){
        if(g.date!==date||have.has(String(g.id)))continue;
        extra.push({gid:g.id,away:g.away,home:g.home,date:g.date,start:g.time,stages:{},
          score:(g.as_!=null||g.hs!=null)?{away:g.as_??0,home:g.hs??0}:null,ended:g.end||null});
      }
    }
    const startKey=g=>{const m=String(g.start||'').match(/(\d{1,2}):(\d{2})\s*(AM|PM)/i);if(!m)return 9e4+g.gid;let h=+m[1]%12;if(/pm/i.test(m[3]))h+=12;return h*60+ +m[2]};
    return fromIdx.concat(extra).sort((a,b)=>startKey(a)-startKey(b)||a.gid-b.gid);
  };
  const pickGid=(list,prefer)=>{if(prefer&&list.some(g=>g.gid===prefer))return prefer;const hit=list.find(hasB);return (hit||list[0]||{}).gid};
  const st={date:q.get('ladate')||etToday(),gid:+(q.get('lagame'))||null,stage:q.get('lastage')||null,team:'all',role:'all',props:false};
  let games=gamesOn(st.date);if(!st.gid)st.gid=pickGid(games);
  const heads={};(D0&&D0.players||[]).forEach(p=>heads[p.id]=p.head);
  const top=()=>`<div class="la-top"><h2 style="margin:0">⏱️ Live Analyzer</h2><span class="la-prev">BETA · UNCALIBRATED</span><span class="m small">Intermission ratings and live-bet board. Built from official play-by-play and shift data.</span></div>`;
  const dateBar=()=>{
    const td=etToday();const dates=allDates();const i=dates.indexOf(st.date);
    const prev=i>0?dates[i-1]:null,next=(i>=0&&i<dates.length-1)?dates[i+1]:null;
    const anchors=[shiftDate(td,-1),td,shiftDate(td,1)];
    const shown=[...new Set([st.date,...anchors])].filter(Boolean).sort();
    const chip=d=>`<a class="${d===st.date?'on':''}" data-ladate="${d}"><span>${esc(relLabel(d,td))}</span><span class="la-dsub">${esc(fmtDay(d))}</span></a>`;
    return `<div class="la-dates" role="group" aria-label="Filter by date"><a class="la-arr${prev?'':' off'}" data-lashift="-1" aria-label="Previous date">‹</a>${shown.map(chip).join('')}<a class="la-arr${next?'':' off'}" data-lashift="1" aria-label="Next date">›</a></div>`;
  };
  const strip=G=>dateBar()+`<div class="la-games">${games.length?games.map(g=>`<a class="${G&&g.gid===G.gid?'on':''}" data-gid="${g.gid}">${esc(g.away)} @ ${esc(g.home)} <span style="opacity:.7">${hasB(g)?(g.score?g.score.away+'–'+g.score.home:'')+(g.ended&&g.ended!=='REG'?' '+g.ended:''):(g.start?esc(g.start):'pending')}</span></a>`).join(''):'<span class="m small">No games on '+esc(fmtDay(st.date))+'.</span>'}</div>`;
  const setDate=d=>{st.date=d;games=gamesOn(st.date);st.gid=pickGid(games);st.stage=null;draw()};
  const wire=()=>{
    el.querySelectorAll('[data-gid]').forEach(a=>a.onclick=()=>{st.gid=+a.dataset.gid;st.stage=null;draw()});
    el.querySelectorAll('[data-ladate]').forEach(a=>a.onclick=()=>{if(a.dataset.ladate!==st.date)setDate(a.dataset.ladate)});
    el.querySelectorAll('[data-lashift]').forEach(a=>a.onclick=()=>{const dates=allDates();const i=dates.indexOf(st.date);const n=dates[i+ +a.dataset.lashift];if(n)setDate(n)});
  };
  async function draw(){
    games=gamesOn(st.date);
    const G=games.find(g=>g.gid===st.gid)||IDX.games[String(st.gid)]||games[0];
    if(!G){el.innerHTML=top()+strip(null)+`<div class="card"><p style="margin:0">No games on ${esc(fmtDay(st.date))}.</p></div>`+METH;wire();return}
    if(!hasB(G)){el.innerHTML=top()+strip(G)+`<div class="card"><b>${esc(G.away)} @ ${esc(G.home)}</b>${G.start?' · '+esc(G.start)+' ET':''}<p class="small m" style="margin:6px 0 0">No board yet. Boards appear at the end of the 1st and 2nd period, and a final board after the game ends. This page updates by itself.</p></div>`+METH;wire();return}
    if(!G.stages[st.stage])st.stage=latestStage(G);
    const D=await J(G.stages[st.stage].file);D._head=heads;D.gid=G.gid;
    el.innerHTML=top()+strip(G)+`
    <div class="la-stage">${['p1','p2','reg','final'].map(s=>{const has=G.stages[s];const lab=s==='reg'?(has&&D.ot?'OT view (tied after 3)':'End of 3rd'):SN[s];return `<a class="${s===st.stage?'on':''}${has?'':' off'}" data-stage="${s}">${lab}</a>`}).join('')}</div>
    <div class="card"><div class="la-score"><span class="tm">${esc(D.away)}</span><b>${D.score.away} – ${D.score.home}</b><span class="tm">${esc(D.home)}</span><span class="m small">${D.stage==='final'?'Final'+(D.ended&&D.ended!=='REG'?' ('+D.ended+')':''):SN[D.stage]} · board built ${esc((D.built||'').replace('T',' ').slice(0,16))} ET</span></div>
    <div class="small m" style="margin-top:6px">Possession is shown as on-ice 5v5 shot-attempt share (a proxy). ${D.degraded?'<div class="note" style="margin:8px 0 2px">⚡ Early read: the official shift chart is still posting for this period, so ice time comes from the live box score and shot-share (possession proxy) covers only the part of the period the shifts reach. This board is rebuilt automatically once the shift data is complete.</div>':''}Shift data coverage: ${Object.entries(D.shiftCoverage||{}).map(([p,s])=>`P${p} ${s>=1195?'complete':mm(s)}`).join(', ')||'n/a'}.${D.absent&&D.absent.length?` ⚠️ ${D.absent.length} skater(s) have not played this period (possible injury).`:''}</div></div>
    ${boardHTML(D,grades,D.stage)}${otHTML(D)}${D.stage==='final'?finalNote(D,grades,G):''}${tableHTML(D,st)}${METH}`;
    wire();
    el.querySelectorAll('[data-stage]').forEach(a=>a.onclick=()=>{st.stage=a.dataset.stage;draw()});
    el.querySelectorAll('[data-la]').forEach(c=>c.onchange=()=>{const k=c.dataset.la;st[k]=k==='props'?c.checked:c.value;draw()});
    try{window.sortable&&sortable(el)}catch(e){}
  }
  function finalNote(D,grades,G){
    if(!grades)return '';const gs=grades.filter(x=>x.gid===D.gid&&x.items.length);if(!gs.length)return '';
    const rows=gs.map(g=>{const hits=g.items.filter(i=>i.hit===true).length,n=g.items.filter(i=>i.hit!=null).length;return `<tr><td class="l">${SN[g.stage]} board → ${g.span}</td><td>${g.items.length}</td><td>${n?hits+'/'+n:'–'}</td></tr>`}).join('');
    return `<div class="card"><h3>What happened after the boards <span class="m small">(this game, illustration only, not a backtest)</span></h3><table><thead><tr><th>Board</th><th>Players listed</th><th>Goal/point hits</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  }
  await draw();
  const iv=setInterval(async()=>{if(!el.isConnected){clearInterval(iv);return}if(document.hidden)return;
    try{const n=await J('index.json');if(n.updated&&n.updated!==IDX.updated){IDX=n;games=gamesOn(st.date);const y=scrollY;await draw();scrollTo(0,y)}}catch(e){}},60000);
};
})();
