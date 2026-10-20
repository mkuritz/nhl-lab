/* NHL Lab: Goalie Matchup + Shot Map. Official NHL play-by-play shot x/y; xG from the Sports Labs shot model. */
(function(){
const ZN={slot:'Slot (high danger)',inner:'Inner circles (mid danger)',perim:'Perimeter / behind net (low)',point:'Point (low danger)'},ZK=['slot','inner','perim','point'],DG={slot:'High',inner:'Mid',perim:'Low',point:'Low'};
const TYN={wrist:'Wrist',snap:'Snap',slap:'Slap','tip-in':'Tip-in',backhand:'Backhand',deflected:'Deflection','wrap-aroun':'Wrap-around',bat:'Batted',poke:'Poke','between-le':'Between legs',cradle:'Cradle',other:'Other'};
const MIN_G=100,MIN_S=30;
const zone=(x,y)=>x>89?'perim':(x>=69&&Math.abs(y)<=9)?'slot':(x>=54&&Math.abs(y)<=22)?'inner':x>=54?'perim':'point';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const sv3=v=>v==null||isNaN(v)?'–':(v>=1?'1.000':v.toFixed(3).replace(/^0/,''));const pc=(v,d=1)=>v==null||isNaN(v)?'–':(v*100).toFixed(d)+'%';
const sg=(v,d=1)=>v==null||isNaN(v)?'–':(v>0?'+':'')+v.toFixed(d);
let IDX=null;const cache={};
async function J(u){if(cache[u])return cache[u];const r=await fetch(u+(u.includes('?')?'&':'?')+'v='+(IDX?.updated||Date.now()).toString().replace(/\W/g,''));if(!r.ok)throw new Error(r.status);return cache[u]=await r.json()}
const CSS=`<style id="smcss">#smbox{max-width:100%;overflow-x:clip}
.sm-wrap>div,.sm-main>div{min-width:0}.sm-x{overflow-x:auto}.sm-wrap{display:grid;grid-template-columns:minmax(0,1fr) 250px;gap:14px}.sm-main{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(0,1fr);gap:0;padding:0;overflow:hidden}
.sm-main>div{padding:14px}.sm-main>div+div{border-left:1px solid var(--b)}.sm-side .card{margin-bottom:12px}.sm-big{font-size:30px;font-weight:800;line-height:1.1}.sm-lab{font-size:12px;color:var(--m)}
.sm-rink{position:relative;width:100%;touch-action:manipulation}.sm-rink svg{width:100%;height:auto;display:block;border-radius:14px}
.sm-tip{position:absolute;pointer-events:none;background:#0b1020ee;border:1px solid var(--b);border-radius:8px;padding:6px 9px;font-size:12px;white-space:nowrap;z-index:3;display:none;box-shadow:0 6px 20px #0008}
.sm-seg{display:inline-flex;border:1px solid var(--b);border-radius:99px;overflow:hidden}.sm-seg a{padding:5px 11px;font-size:12px;font-weight:700;color:var(--m)}.sm-seg a.on{background:var(--a);color:#000}
.sm-chipbar{display:flex;gap:8px;overflow-x:auto;padding-bottom:6px;margin-bottom:12px}.sm-game{flex:0 0 auto;background:var(--p);border:1px solid var(--b);border-radius:12px;padding:8px 10px;font-size:12px}
.sm-game a{display:block;padding:3px 6px;border-radius:6px;color:var(--t)}.sm-game a.on{background:var(--a);color:#000}.sm-game .h{color:var(--m);font-weight:700;margin-bottom:2px}
.sm-st{display:inline-block;font-size:11px;font-weight:800;padding:3px 10px;border-radius:99px}.sm-st.c{background:#0c2b20;color:var(--g);border:1px solid #1d6b4c}.sm-st.p{background:#2a2205;color:var(--y);border:1px solid #6b5512}
.sm-zt td,.sm-zt th{padding:6px 5px}.sm-zbar{height:6px;border-radius:3px;background:var(--p2);overflow:hidden}.sm-zbar i{display:block;height:100%}
.sm-legend{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--m);margin-top:6px}.sm-legend i{flex:1;height:7px;border-radius:4px;background:linear-gradient(90deg,#2c7bff,#22d3ee,#facc15,#ff3b3b)}
.sm-ok{color:var(--g)}.sm-bad{color:var(--r)}.sm-score{display:inline-flex;align-items:center;justify-content:center;width:64px;height:64px;border-radius:50%;font-weight:900;font-size:22px;border:4px solid}
.sm-search{position:relative;min-width:220px;flex:1;max-width:340px}.sm-search ul{position:absolute;z-index:7;left:0;right:0;max-height:260px;overflow:auto;background:var(--p);border:1px solid var(--b);border-radius:8px;margin:4px 0 0;padding:0;list-style:none}.sm-search li{padding:8px 10px;cursor:pointer;border-bottom:1px solid var(--b)}.sm-search li:hover{background:var(--p2)}
@media(max-width:980px){.sm-wrap{grid-template-columns:minmax(0,1fr)}.sm-side{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.sm-side .card{margin:0}}
@media(max-width:760px){.sm-main{grid-template-columns:minmax(0,1fr)}.sm-main>div+div{border-left:0;border-top:1px solid var(--b)}.sm-big{font-size:24px}}
</style>`;
// ---------- rink ----------
const X0=0,X1=100,W=X1-X0,H=85;
const px=x=>x-X0,py=y=>42.5-y;
function rinkSVG(id){const c=(x,y,r,s,f='none',w=.35)=>`<circle cx="${px(x)}" cy="${py(y)}" r="${r}" stroke="${s}" stroke-width="${w}" fill="${f}"/>`;
 const fo=y=>c(69,y,15,'#c8313b')+c(69,y,.9,'#c8313b','#c8313b')+`<path d="M${px(67)} ${py(y)-.8}h-2M${px(71)} ${py(y)-.8}h2M${px(67)} ${py(y)+.8}h-2M${px(71)} ${py(y)+.8}h2" stroke="#c8313b" stroke-width=".3"/>`;
 return `<svg viewBox="0 0 ${W} ${H}" id="${id}" role="img" aria-label="Half-rink shot map"><defs><clipPath id="${id}c"><path d="M0 0H72a28 28 0 0 1 28 28V57a28 28 0 0 1-28 28H0Z"/></clipPath>
 <linearGradient id="${id}ice" x1="0" x2="1"><stop offset="0" stop-color="#e9f0f7"/><stop offset="1" stop-color="#f4f8fc"/></linearGradient></defs>
 <g clip-path="url(#${id}c)"><rect width="${W}" height="${H}" fill="url(#${id}ice)"/><g id="${id}z"></g><image id="${id}h" x="0" y="0" width="${W}" height="${H}" preserveAspectRatio="none" />
 <line x1=".4" y1="0" x2=".4" y2="${H}" stroke="#c8313b" stroke-width=".9"/><line x1="${px(25)}" y1="0" x2="${px(25)}" y2="${H}" stroke="#1f5fbf" stroke-width="1.1"/><line x1="${px(89)}" y1="0" x2="${px(89)}" y2="${H}" stroke="#c8313b" stroke-width=".35"/>
 ${c(0,0,15,'#1f5fbf')}${c(20,22,.9,'#c8313b','#c8313b')}${c(20,-22,.9,'#c8313b','#c8313b')}${fo(22)}${fo(-22)}
 <path d="M${px(89)} ${py(4)}A6 6 0 0 0 ${px(89)} ${py(-4)}" fill="#7fb5ff66" stroke="#c8313b" stroke-width=".3" transform="translate(0,0)"/>
 <path d="M${px(89)} ${py(4)} A6 6 0 0 0 ${px(89)} ${py(-4)}Z" fill="none"/>
 <rect x="${px(89)}" y="${py(3)}" width="3.3" height="6" fill="#fff" stroke="#c8313b" stroke-width=".4"/>
 <path d="M${px(89)} ${py(11)}L${px(100)} ${py(14)}M${px(89)} ${py(-11)}L${px(100)} ${py(-14)}" stroke="#c8313b" stroke-width=".3"/>
 <g id="${id}d"></g><g id="${id}hl"></g></g><path d="M0 .3H72a27.7 27.7 0 0 1 27.7 27.7V57a27.7 27.7 0 0 1-27.7 27.7H0" fill="none" stroke="#9fb1c8" stroke-width=".6"/></svg>`}
const zonePath=z=>{const P={slot:`M${px(69)} ${py(9)}H${px(89)}V${py(-9)}H${px(69)}Z`,
 inner:`M${px(54)} ${py(22)}H${px(89)}V${py(9)}H${px(69)}V${py(-9)}H${px(89)}V${py(-22)}H${px(54)}Z`,
 perim:`M${px(54)} 0H${W}V${H}H${px(54)}V${py(-22)}H${px(89)}V${py(22)}H${px(54)}Z`,point:`M${px(25)} 0H${px(54)}V${H}H${px(25)}Z`};return P[z]};
function heatImage(shots,mode){const S=4,cw=W*S,ch=H*S,cv=document.createElement('canvas');cv.width=cw;cv.height=ch;const g=cv.getContext('2d');
 const grid=new Float32Array(cw*ch),sig=4.2*S,R=Math.ceil(sig*2.6),k=[];for(let d=-R;d<=R;d++)k.push(Math.exp(-d*d/(2*sig*sig)));
 const tmp=new Float32Array(cw*ch);let any=0;
 for(const s of shots){const w=mode==='goals'?(s[4]===2?1:0):mode==='xg'?(s[5]||0):1;if(!w)continue;any=1;const ix=Math.round(px(s[0])*S),iy=Math.round(py(s[1])*S);if(ix>=0&&ix<cw&&iy>=0&&iy<ch)tmp[iy*cw+ix]+=w}
 if(!any)return null;
 const t2=new Float32Array(cw*ch);for(let y=0;y<ch;y++)for(let x=0;x<cw;x++){const v=tmp[y*cw+x];if(!v)continue;for(let d=-R;d<=R;d++){const xx=x+d;if(xx>=0&&xx<cw)t2[y*cw+xx]+=v*k[d+R]}}
 let mx=0;for(let x=0;x<cw;x++)for(let y=0;y<ch;y++){const v=t2[y*cw+x];if(!v)continue;for(let d=-R;d<=R;d++){const yy=y+d;if(yy>=0&&yy<ch){const o=yy*cw+x;grid[o]+=v*k[d+R];if(grid[o]>mx)mx=grid[o]}}}
 const im=g.createImageData(cw,ch),st=[[0,[44,123,255]],[.35,[34,211,238]],[.65,[250,204,21]],[1,[255,59,59]]];
 for(let i=0;i<grid.length;i++){const v=Math.pow(grid[i]/mx,.75);if(v<.04)continue;let a=st[0],b=st[st.length-1];for(let j=0;j<st.length-1;j++)if(v>=st[j][0]&&v<=st[j+1][0]){a=st[j];b=st[j+1];break}
  const t=(v-a[0])/((b[0]-a[0])||1),o=i*4;for(let c=0;c<3;c++)im.data[o+c]=a[1][c]+(b[1][c]-a[1][c])*t;im.data[o+3]=Math.min(235,40+v*230)}
 g.putImageData(im,0,0);return cv.toDataURL()}
function svColor(d){/* d = goalie SV - league SV; negative = weak (red) */const t=Math.max(-1,Math.min(1,d/0.04));return t<0?`rgba(255,70,70,${.18+(-t)*.45})`:`rgba(40,120,255,${.15+t*.4})`}
function drawRink(id,shots,opt){if(!document.getElementById(id))return;const im=document.getElementById(id+'h'),dg=document.getElementById(id+'d'),zg=document.getElementById(id+'z');if(!im)return;
 const url=heatImage(shots,opt.mode);url?im.setAttribute('href',url):im.removeAttribute('href');
 zg.innerHTML=opt.zfill?ZK.map(z=>opt.zfill[z]?`<path d="${zonePath(z)}" fill="${opt.zfill[z]}" stroke="#ffffff99" stroke-width=".25" stroke-dasharray="1 1"/>`:'').join(''):ZK.map(z=>`<path d="${zonePath(z)}" fill="none" stroke="#5b6b8a55" stroke-width=".25" stroke-dasharray="1 1"/>`).join('');
 const goals=shots.filter(s=>s[4]===2),saves=opt.dots==='all'?shots.filter(s=>s[4]!==2):[];
 dg.innerHTML=saves.map(s=>`<circle cx="${px(s[0])}" cy="${py(s[1])}" r=".55" fill="#1e293b" fill-opacity=".35"/>`).join('')+goals.map(s=>`<circle cx="${px(s[0])}" cy="${py(s[1])}" r="1.15" fill="#fff" stroke="#0b1020" stroke-width=".35"/>`).join('')}
function hookTip(id,getShots,zoneInfo){const svg=document.getElementById(id);if(!svg)return;const wrap=svg.parentNode,tip=wrap.querySelector('.sm-tip'),hl=document.getElementById(id+'hl');
 const pos=e=>{const r=svg.getBoundingClientRect(),cx=(e.touches?e.touches[0]:e).clientX,cy=(e.touches?e.touches[0]:e).clientY;return{x:(cx-r.left)/r.width*W+X0,y:42.5-(cy-r.top)/r.height*H,lx:cx-wrap.getBoundingClientRect().left,ly:cy-wrap.getBoundingClientRect().top,w:r.width}};
 const show=e=>{const p=pos(e);if(p.x<25||p.x>100){tip.style.display='none';hl.innerHTML='';return}const S=getShots();let best=null,bd=9;
  for(const s of S){const d=(s[0]-p.x)**2+(s[1]-p.y)**2;if(d<bd&&(s[4]===2||d<2.2)){bd=d;best=s}}
  const z=zone(p.x,p.y);let h;
  if(best){h=`<b>${best[4]===2?'🚨 Goal':best[4]===1?'Saved shot':'Missed net'}</b> · ${TYN[best[2]]||esc(best[2])} · ${best[3]}${best[7]?' · rebound':''}<br>xG ${best[5]==null?'–':best[5].toFixed(2)} · ${Math.round(Math.hypot(89-best[0],best[1]))} ft · ${esc(IDX.games[best[6]]?.[1]||'')}`;hl.innerHTML=`<circle cx="${px(best[0])}" cy="${py(best[1])}" r="2" fill="none" stroke="#0b1020" stroke-width=".5"/>`}
  else{h=zoneInfo(z);hl.innerHTML=`<path d="${zonePath(z)}" fill="#ffffff22" stroke="#0b1020" stroke-width=".4"/>`}
  tip.innerHTML=h;tip.style.display='block';const tw=tip.offsetWidth;tip.style.left=Math.max(0,Math.min(p.lx+12,wrap.offsetWidth-tw))+'px';tip.style.top=Math.max(0,p.ly-tip.offsetHeight-10)+'px'};
 svg.addEventListener('mousemove',show);svg.addEventListener('touchstart',show,{passive:true});svg.addEventListener('mouseleave',()=>{tip.style.display='none';hl.innerHTML=''})}
// ---------- stats ----------
function zoneStats(S){const o={};for(const z of ZK)o[z]={sa:0,ga:0,xg:0,att:0};for(const s of S){const z=o[zone(s[0],s[1])];z.att++;z.xg+=s[5]||0;if(s[4]>=1){z.sa++;if(s[4]===2)z.ga++}}return o}
function spark(v,col='#4fc3ff',w=120,h=30,ref){if(!v.length)return '<span class="m small">–</span>';const mn=Math.min(...v,ref??Infinity),mx=Math.max(...v,ref??-Infinity),r=(mx-mn)||1,X=i=>v.length<2?w/2:i/(v.length-1)*w,Y=x=>h-3-(x-mn)/r*(h-6);
 return `<svg viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" style="vertical-align:middle">${ref!=null?`<line x1="0" x2="${w}" y1="${Y(ref)}" y2="${Y(ref)}" stroke="#8d97b8" stroke-dasharray="2 2" stroke-width="1"/>`:''}<polyline points="${v.map((x,i)=>X(i)+','+Y(x)).join(' ')}" fill="none" stroke="${col}" stroke-width="2"/>${v.map((x,i)=>`<circle cx="${X(i)}" cy="${Y(x)}" r="2" fill="${col}"/>`).join('')}</svg>`}
const seg=(name,cur,opts)=>`<span class="sm-seg" data-k="${name}">${opts.map(([k,l])=>`<a data-v="${k}" class="${k===cur?'on':''}">${l}</a>`).join('')}</span>`;
const typeSel=(cur)=>`<select data-k="type">${[['all','All shot types'],...Object.entries(TYN).filter(([k])=>k!=='other'&&k!=='cradle')].map(([k,l])=>`<option value="${k}"${k===cur?' selected':''}>${l}</option>`).join('')}</select>`;
function searchBox(ph,list,href){return `<div class="sm-search"><input placeholder="${ph}" style="width:100%" data-list="${list}" data-href="${href}"><ul hidden></ul></div>`}
function wireSearch(root){root.querySelectorAll('.sm-search input').forEach(inp=>{const ul=inp.nextElementSibling,L=inp.dataset.list==='g'?IDX.goalies:IDX.skaters;
 inp.addEventListener('input',()=>{const q=inp.value.trim().toLowerCase();if(q.length<2){ul.hidden=true;return}const m=L.filter(r=>(r[1]||'').toLowerCase().includes(q)).slice(0,12);ul.innerHTML=m.map(r=>`<li data-id="${r[0]}">${esc(r[1])} <span class="m small">${esc(r[2]||'')}</span></li>`).join('')||'<li class="m">No match</li>';ul.hidden=false});
 ul.addEventListener('click',e=>{const li=e.target.closest('li[data-id]');if(li)location.hash=inp.dataset.href+li.dataset.id})})}
function wireFilters(root,st,rerender){root.querySelectorAll('.sm-seg').forEach(sgm=>sgm.addEventListener('click',e=>{const a=e.target.closest('a[data-v]');if(!a)return;st[sgm.dataset.k]=a.dataset.v;rerender()}));
 root.querySelectorAll('select[data-k]').forEach(s=>s.addEventListener('change',()=>{st[s.dataset.k]=s.value;rerender()}))}
function filt(rows,st,games){let R=rows;if(st.str==='5v5')R=R.filter(s=>s[3]==='5v5');else if(st.str==='PP')R=R.filter(s=>s[3]==='PP');if(st.type&&st.type!=='all')R=R.filter(s=>s[2]===st.type);
 if(st.span==='season')R=R.filter(s=>IDX.games[s[6]][4]===1);else if(st.span==='prev')R=R.filter(s=>IDX.games[s[6]][4]===0);else if(st.span==='l10'){const set=new Set(games.slice(-10));R=R.filter(s=>set.has(s[6]))}return R}
const SPANS=[['l10','Last 10'],['season','This season'],['prev','Last season']],STRS=[['all','All'],['5v5','5v5'],['PP','PP']],MODES=[['shots','Shots'],['goals','Goals'],['xg','xG']];
// ---------- goalie view ----------
async function goalieView(el,arg,ctx){const T=IDX.tonight;let id=+arg;if(!id){const f=T.find(g=>g.g.away.id)||{};id=f.g?.away?.id}
 const chips=T.map(g=>`<div class="sm-game"><div class="h">${esc(g.away)} @ ${esc(g.home)}</div>${['away','home'].map(s=>{const x=g.g[s];return x.id?`<a href="#goaliemap/${x.id}" class="${x.id===id?'on':''}">${esc(x.name.split(' ').slice(-1)[0])} <span style="opacity:.75">${x.status==='Confirmed'?'✓':'proj'}</span></a>`:`<a class="m">${esc(x.name||'TBD')}</a>`}).join('')}</div>`).join('');
 let G=null;try{G=id?await J(`data/shotmap/g/${id}.json`):null}catch(e){}
 const head=`<h2>🥅 Goalie Matchup <span class="m small" style="font-weight:400">· ${esc(IDX.day)} · updated ${esc(IDX.updated)}</span></h2><div class="sm-chipbar">${chips||'<span class="m">No games scheduled today.</span>'}</div>
 <div class="filters">${searchBox('Find any goalie…','g','#goaliemap/')}</div>`;
 if(!G){el.innerHTML=CSS+head+'<div class="card m">Not enough data yet: no shots against logged for this goalie in the last two seasons.</div>';wireSearch(el);return}
 const tg=T.find(g=>g.g.away.id===id||g.g.home.id===id),side=tg?(tg.g.away.id===id?'away':'home'):null,me=tg?tg.g[side]:null;
 const st={span:G.games.filter(g=>IDX.games[g[0]][4]).length>=3?'season':'prev',str:'all',type:'all',mode:'shots',dots:'goals',tint:'off'};const gi=G.games.map(g=>g[0]);
 const render=()=>{const S=filt(G.shots,st,gi),Z=zoneStats(S),sa=S.filter(s=>s[4]>=1).length,ga=S.filter(s=>s[4]===2).length,ok=sa>=MIN_G;
  const lg=IDX.lg[st.span==='prev'?'prev':'cur'];const L10=G.games.slice(-10),gs10=L10.reduce((t,g)=>t+g[5]-g[4],0),sa10=L10.reduce((t,g)=>t+g[3],0);
  const hd=Z.slot,hdsv=hd.sa?1-hd.ga/hd.sa:null;
    // scoring lift vs this goalie: league shot mix weights, goalie zone SV vs league (selected span)
  let mix={},tot=0;for(const z of ZK){mix[z]=IDX.lgMix[z]}
  let lift=null;if(ok){lift=0;for(const z of ZK){const zs=Z[z];const K=40,gsv=(zs.sa-zs.ga+K*lg[z])/(zs.sa+K);lift+=mix[z]*((1-gsv)-(1-lg[z]))}}
  const zfill={};for(const z of ZK){const zs=Z[z];zfill[z]=ok&&zs.sa>=15?svColor((1-zs.ga/zs.sa)-lg[z]):null}
  const per=L10.map(g=>g[3]?1-g[4]/g[3]:null).filter(v=>v!=null);
  el.innerHTML=CSS+head+`<div class="filters">${seg('span',st.span,SPANS)}${seg('str',st.str,STRS)}${typeSel(st.type)}${seg('mode',st.mode,MODES)}${seg('dots',st.dots,[['goals','Goal dots'],['all','All dots']])}${seg('tint',st.tint,[['off','Heat'],['on','Zone SV% tint']])}</div>
  <div class="sm-wrap"><div><div class="card sm-main"><div><h3>${esc(G.name)} <span class="m small">${esc(G.team||'')}</span> · shot-location heat map <span class="m small">(shots against${st.mode==='goals'?', goals only':st.mode==='xg'?', weighted by xG':''})</span></h3>
   <div class="sm-rink">${rinkSVG('gr')}<div class="sm-tip"></div></div><div class="sm-legend">Fewer<i></i>More · white dots = goals against · hover or tap the ice</div>
   <p class="small m" style="margin:6px 0 0">${S.length} unblocked attempts · ${sa} shots on goal · ${ga} goals${st.str==='PP'?' (opponent on the power play)':''}. Empty-net shots excluded. All shots drawn toward the same net.</p></div>
   <div><h3>Save % by zone</h3>${ok?`<div class="sm-x"><table class="sm-zt"><tr><th class="l">Zone</th><th>SV%</th><th>Lg</th><th>SA</th></tr>${ZK.map(z=>{const zs=Z[z],v=zs.sa?1-zs.ga/zs.sa:null,d=v==null?null:v-lg[z];return `<tr><td class="l">${ZN[z]}<div class="sm-zbar"><i style="width:${Math.min(100,(v||0)*100-70)/30*100}%;background:${d==null?'#555':d<0?'var(--r)':'var(--a)'}"></i></div></td><td class="${d==null?'':d<-0.01?'sm-bad':d>0.01?'sm-ok':''}"><b>${zs.sa<15?'<span class="m">–</span>':sv3(v)}</b></td><td class="m">${sv3(lg[z])}</td><td>${zs.sa}</td></tr>`}).join('')}</table></div>
   <p class="small m">Zones are rink areas (where the shot came from). Free play-by-play has no net-location data (glove/blocker), so we don't show net zones. Turn on "Zone SV% tint" to shade the ice: red = below league in that zone, blue = above. Zones with under 15 shots show –.</p>`:`<p class="m">Not enough data yet: ${sa} shots against in this filter; we need ${MIN_G}+ before showing save % by zone. Try "Last season" or "All".</p>`}</div></div>
   ${G.tonight?watchCard(G):''}</div>
  <div class="sm-side"><div class="card"><div class="sm-lab">GSAx · last 10 games</div><div class="sm-big ${gs10>0?'g':gs10<0?'r':''}">${sa10>=MIN_G?sg(gs10,1):'–'}</div><div class="sm-lab">${sa10>=MIN_G?`Goals saved above expected over his last ${L10.length} appearances (${sa10} shots), Sports Labs shot model`:`Not enough data yet (${sa10} shots)`}</div></div>
   <div class="card"><div class="sm-lab">HD SV% · ${SPANS.find(s=>s[0]===st.span)[1].toLowerCase()}</div><div class="sm-big">${ok&&hd.sa>=15?sv3(hdsv):'–'}</div><div class="sm-lab">Slot shots · league ${sv3(lg.slot)} · ${hd.sa} shots</div></div>
   <div class="card"><div class="sm-lab">SV% trend · last ${per.length}</div>${spark(per,'#4fc3ff',180,40,lg?0.9:null)}<div class="sm-lab">Overall ${ok?sv3(1-ga/sa):'–'} · ${(L10.reduce((t,g)=>t+g[4],0)/Math.max(1,L10.length)).toFixed(2)} GA per appearance (L10)</div>${spark(L10.map(g=>g[4]),'#ff6b7a',180,30)}</div>
   <div class="card">${me?`<span class="sm-st ${me.status==='Confirmed'?'c':'p'}">${me.status==='Confirmed'?'Confirmed starter':'Projected starter'}</span><div class="sm-lab" style="margin-top:8px">${esc(tg.away)} @ ${esc(tg.home)} · ${esc((tg.start||'').replace(/^\w+ \d{4}-\d\d-\d\d /,'').replace(/ \(UTC.*$/,''))}<br>${me.b2b?'<b class="y">Back-to-back</b>':me.rest!=null?`${me.rest} day${me.rest===1?'':'s'} rest`:''}</div>`:'<span class="m small">Not starting tonight</span>'}</div>
   <div class="card"><div class="sm-lab">Scoring lift vs this goalie</div><div class="sm-big ${lift>0?'g':lift<0?'r':''}">${lift==null?'–':sg(lift*100,1)+'%'}</div><div class="sm-lab">Change in goals per shot on goal vs a league-average goalie, league shot mix, zones shrunk toward league. Positive = easier to score on.</div></div>
  </div></div>`;
  drawRink('gr',S,{mode:st.mode,dots:st.dots,zfill:ok&&st.tint==='on'?zfill:null});
  hookTip('gr',()=>S,z=>{const zs=Z[z],v=zs.sa?1-zs.ga/zs.sa:null;return `<b>${ZN[z]}</b><br>${zs.sa} SA · ${zs.ga} GA · SV ${zs.sa>=15?sv3(v):'–'} (lg ${sv3(lg[z])})<br>xGA ${zs.xg.toFixed(1)}`});
  wireFilters(el,st,render);wireSearch(el)};
 render()}
function watchCard(G){const W=G.tonight.watch||[];return `<div class="card"><h3>Opponent shooters to watch <span class="m small">(${esc(G.tonight.opp)})</span></h3>
 ${W.length?`<div class="tw"><table><tr><th class="l">Skater</th><th>Fav zone</th><th>Match</th><th>SOG/GP</th><th>Our anytime goal</th><th>Edge</th></tr>${W.map(r=>`<tr><td class="l"><a href="#shotmap/${r.id}">${esc(r.name)}</a> <span class="m small">${esc(r.pos||'')}</span></td><td class="small">${esc(ZN[r.fav].split(' (')[0])}</td><td><b class="${r.m>=55?'g':r.m<=45?'r':''}">${r.m}</b></td><td>${r.sogpg.toFixed(1)}</td><td>${r.pG==null?'<span class="m">–</span>':pc(r.pG,0)}</td><td>${r.eG==null?'<span class="m small">no price</span>':`<span class="${r.eG>0?'g':'r'}">${sg(r.eG*100,1)}%</span>`}</td></tr>`).join('')}</table></div>
 <p class="small m">Ranked by how well each shooter's shot locations line up with this goalie's weaker zones, times shot volume (this season counts double). Match 50 = average goalie. Edge shows only when a same-day price exists.</p>`:'<p class="m">Not enough data yet for the opposing skaters.</p>'}</div>`}
// ---------- scorer view ----------
async function scorerView(el,arg,ctx){let id=+arg;const D=ctx.D||{};
 if(!id){const r=(D.slate?.rows||[]).filter(r=>r.date===IDX.day).sort((a,b)=>b.pG-a.pG)[0];id=r?.pid||IDX.skaters[0]?.[0]}
 const top=(D.slate?.rows||[]).filter(r=>r.date===IDX.day).sort((a,b)=>b.pG-a.pG).slice(0,8);
 const head=`<h2>🎯 Shot Map <span class="m small" style="font-weight:400">· updated ${esc(IDX.updated)}</span></h2><div class="filters">${searchBox('Find a skater…','s','#shotmap/')}${top.map(r=>`<a class="pill" href="#shotmap/${r.pid}" style="${r.pid===id?'background:var(--a);color:#000':''}">${esc(r.name.split(' ').slice(-1)[0])} ${pc(r.pG,0)}</a>`).join('')}</div>`;
 let P=null;try{P=await J(`data/shotmap/s/${id}.json`)}catch(e){}
 if(!P){el.innerHTML=CSS+head+'<div class="card m">Not enough data yet: no shot attempts logged for this skater in the last two seasons.</div>';wireSearch(el);return}
 const st={span:P.games.filter(g=>IDX.games[g][4]).length>=3?'season':'prev',str:'all',type:'all',mode:'shots',dots:'goals'};
 const render=()=>{const S=filt(P.shots,st,P.games),Z=zoneStats(S),sog=S.filter(s=>s[4]>=1).length,g=S.filter(s=>s[4]===2).length,xg=S.reduce((t,s)=>t+(s[5]||0),0),ok=sog>=MIN_S;
  const tt=st.span==='prev'?P.toi.prev:P.toi.cur;const ng=st.span==='l10'?Math.min(10,P.games.length):st.span==='season'?(P.toi.cur[0]||0):(P.toi.prev[0]||0);
  const toiMin=st.str==='PP'?(tt[2]||0)*ng:st.str==='5v5'?Math.max(0,(tt[1]||0)-(tt[2]||0))*ng:(tt[1]||0)*ng;const s60=toiMin>0?sog/toiMin*60:null;
  const split=k=>{const R=filt(P.shots,{...st,str:k},P.games),a=R.filter(s=>s[4]>=1).length,gg=R.filter(s=>s[4]===2).length,x=R.reduce((t,s)=>t+(s[5]||0),0),tm=k==='PP'?(tt[2]||0)*ng:Math.max(0,(tt[1]||0)-(tt[2]||0))*ng;return{a,gg,x,s60:tm?a/tm*60:null}};
  const pp=split('PP'),ev=split('5v5');const L=P.games.slice(-10),per=L.map(gi=>{const R=P.shots.filter(s=>s[6]===gi);return{gi,s:R.filter(s=>s[4]>=1).length,g:R.filter(s=>s[4]===2).length,x:R.reduce((t,s)=>t+(s[5]||0),0)}});
  const T=P.tonight,M=T?.match;const fav=M?ZK.slice().sort((a,b)=>M.zones[b].share-M.zones[a].share):[];
  const sc=M?.score,scol=sc==null?'#8d97b8':sc>=55?'#3ddc97':sc<=45?'#ff6b7a':'#ffc857';
  el.innerHTML=CSS+head+`<div class="card hero" style="gap:16px"><div style="flex:1"><h2 style="margin:0"><a href="#player/${P.id}" style="color:var(--t)">${esc(P.name)}</a> <span class="m small">${esc(P.team)} · ${esc(P.pos)}</span></h2>
   <div class="m small">${T?`Tonight vs ${esc(T.opp)} · faces ${esc(T.goalie.name)} <span class="sm-st ${T.goalie.status==='Confirmed'?'c':'p'}">${T.goalie.status}</span>`:'Not playing today'}</div></div>
   ${M?`<div style="text-align:center"><div class="sm-score" style="border-color:${scol};color:${scol}">${sc}</div><div class="sm-lab">Matchup score</div></div>`:''}
   ${T&&T.pG!=null?`<div style="text-align:center"><div class="sm-big">${pc(T.pG,0)}</div><div class="sm-lab">Our anytime goal${T.eG!=null?` · edge <span class="${T.eG>0?'g':'r'}">${sg(T.eG*100,1)}%</span>`:''}</div></div>`:''}</div>
  <div class="filters">${seg('span',st.span,SPANS)}${seg('str',st.str,STRS)}${typeSel(st.type)}${seg('mode',st.mode,MODES)}${seg('dots',st.dots,[['goals','Goal dots'],['all','All dots']])}</div>
  <div class="sm-wrap"><div><div class="card sm-main"><div><h3>Shot heat map <span class="m small">(${st.mode==='goals'?'goals':st.mode==='xg'?'weighted by xG':'all unblocked attempts'})</span></h3><div class="sm-rink">${rinkSVG('sr')}<div class="sm-tip"></div></div>
   <div class="sm-legend">Fewer<i></i>More · white dots = goals · hover or tap the ice</div><p class="small m" style="margin:6px 0 0">${S.length} attempts · ${sog} on goal · ${g} goals · ${xg.toFixed(1)} xG</p></div>
   <div><h3>Shooting % by zone</h3>${ok?`<div class="sm-x"><table class="sm-zt"><tr><th class="l">Zone</th><th>Share</th><th>SH%</th><th>G</th></tr>${ZK.map(z=>{const zs=Z[z],v=zs.sa?zs.ga/zs.sa:null,lgv=1-IDX.lg.all[z];return `<tr><td class="l">${ZN[z]}<div class="sm-zbar"><i style="width:${S.length?zs.att/S.length*100:0}%;background:var(--a)"></i></div></td><td>${S.length?pc(zs.att/S.length,0):'–'}</td><td class="${v==null||zs.sa<10?'':v>lgv+.02?'sm-ok':v<lgv-.02?'sm-bad':''}"><b>${zs.sa<10?'–':pc(v,1)}</b><div class="small m">lg ${pc(lgv,1)}</div></td><td>${zs.ga}</td></tr>`}).join('')}</table></div>`:`<p class="m">Not enough data yet: ${sog} shots on goal in this filter (need ${MIN_S}+). Try a wider span.</p>`}</div></div>
   <div class="card"><h3>Last ${per.length} games with a shot attempt</h3>${trendSVG(per)}<p class="small m">Bars = shots on goal, gold line = xG (own scale), white puck = goals.</p></div>
   ${M?`<div class="card"><h3>Tonight's matchup: ${esc(T.goalie.name)} in ${esc(P.name.split(' ').slice(-1)[0])}'s zones</h3><div class="sm-x"><table><tr><th class="l">Zone</th><th>His share</th><th>Goalie SV%</th><th>League</th><th></th></tr>${fav.map(z=>{const q=M.zones[z],d=q.gsv-q.lsv;return `<tr><td class="l">${ZN[z]}</td><td>${pc(q.share,0)}</td><td class="${d<-0.005?'sm-bad':d>0.005?'sm-ok':''}"><b>${sv3(q.gsv)}</b></td><td class="m">${sv3(q.lsv)}</td><td class="small ${d<-0.005?'g':d>0.005?'r':'m'}">${d<-0.005?'weak spot':d>0.005?'strength':'average'}</td></tr>`}).join('')}</table></div>
   <p class="small m">Expected SH% on his shot mix: <b>${pc(M.vsSh,1)}</b> vs this goalie, ${pc(M.lgSh,1)} vs a league-average goalie. Goalie zone SV% blends this season (double weight) and last, shrunk toward league. Score 50 = neutral.</p></div>`:''}</div>
  <div class="sm-side"><div class="card"><div class="sm-lab">Shots on goal per 60${st.str!=='all'?' · '+st.str:''}</div><div class="sm-big">${s60==null?'–':s60.toFixed(1)}</div><div class="sm-lab">${st.str==='5v5'?'Even-strength TOI approx. (TOI minus PP)':'Season-average TOI'}</div></div>
   <div class="card"><div class="sm-lab">Goals vs xG (finishing luck)</div><div class="sm-big ${g-xg>0?'g':g-xg<0?'r':''}">${sg(g-xg,1)}</div><div class="sm-lab">${g} G on ${xg.toFixed(1)} xG${ok?` · SH% ${pc(sog?g/sog:null,1)}`:''}${Math.abs(g-xg)>=2?(g>xg?' · running hot':' · due on chances'):''}</div></div>
   <div class="card"><div class="sm-lab">PP vs 5v5</div><div class="sm-x"><table class="small"><tr><th class="l"></th><th>SOG</th><th>G</th><th>xG</th><th>/60</th></tr><tr><td class="l">5v5</td><td>${ev.a}</td><td>${ev.gg}</td><td>${ev.x.toFixed(1)}</td><td>${ev.s60==null?'–':ev.s60.toFixed(1)}</td></tr><tr><td class="l">PP</td><td>${pp.a}</td><td>${pp.gg}</td><td>${pp.x.toFixed(1)}</td><td>${pp.s60==null?'–':pp.s60.toFixed(1)}</td></tr></table></div></div>
   <div class="card"><div class="sm-lab">xG per game · last ${per.length}</div>${spark(per.map(r=>r.x),'#ffc857',180,40)}</div></div></div>`;
  drawRink('sr',S,{mode:st.mode,dots:st.dots});
  hookTip('sr',()=>S,z=>{const zs=Z[z];return `<b>${ZN[z]}</b><br>${zs.att} attempts · ${zs.sa} on goal · ${zs.ga} G<br>SH% ${zs.sa>=10?pc(zs.ga/zs.sa,1):'–'} · xG ${zs.xg.toFixed(1)}`});
  wireFilters(el,st,render);wireSearch(el)};
 render()}
function trendSVG(per){if(!per.length)return '<p class="m">No games yet.</p>';const w=560,h=130,n=per.length,bw=w/n,mx=Math.max(4,...per.map(r=>r.s)),Y=v=>h-22-v/mx*(h-34),mxx=Math.max(1,...per.map(r=>r.x)),YX=v=>h-22-v/mxx*(h-34)*.85;
 return `<svg viewBox="0 0 ${w} ${h}" style="width:100%;height:auto">${per.map((r,i)=>`<rect x="${i*bw+bw*.2}" y="${Y(r.s)}" width="${bw*.6}" height="${h-22-Y(r.s)}" rx="3" fill="#4fc3ff55" stroke="#4fc3ff"/><text x="${i*bw+bw/2}" y="${h-8}" fill="#8d97b8" font-size="10" text-anchor="middle">${esc((IDX.games[r.gi]?.[1]||'').slice(5))}</text>${r.g?Array.from({length:r.g},(_,k)=>`<circle cx="${i*bw+bw/2}" cy="${Y(r.s)-7-k*10}" r="4" fill="#fff" stroke="#0b1020"/>`).join(''):''}`).join('')}
 <polyline points="${per.map((r,i)=>`${i*bw+bw/2},${YX(r.x)}`).join(' ')}" fill="none" stroke="#ffc857" stroke-width="2.5"/>${per.map((r,i)=>`<circle cx="${i*bw+bw/2}" cy="${YX(r.x)}" r="3" fill="#ffc857"><title>${r.x.toFixed(2)} xG</title></circle>`).join('')}</svg>`}
window.NHLShot=async function(el,kind,arg,ctx){try{IDX=IDX||await J('data/shotmap/index.json');
 // league shot mix for the goalie "scoring lift" card
 await (kind==='g'?goalieView:scorerView)(el,arg,ctx||{})}catch(e){console.error(e);el.innerHTML='<div class="card m">Shot maps are unavailable right now.</div>'}};
})();
