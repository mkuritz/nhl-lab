/* NHL Lab -> Bet Lab shared slip. Highlighted props map to Bet Lab's NHL props (same keys), then open in Bet Lab's slip. */
(function(){
const LS="nhllab:slip",MK={pG:["Anytime Goal",.5],pP:["Points",.5],p3S:["Shots on Goal",2.5]};
const nm=s=>String(s||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z]/g,"");
let IDX=null,Q=[];try{Q=JSON.parse(localStorage.getItem(LS)||"[]")}catch(e){}
const save=()=>{localStorage.setItem(LS,JSON.stringify(Q));bar()};
fetch("https://betlab.sportslabshq.com/data/props_nhl.json?t="+Date.now()).then(r=>r.ok?r.json():[]).then(d=>{IDX={};(d||[]).forEach(p=>{IDX[nm(p.player)+"|"+p.market+"|"+p.line]=p});if(window.route)route();bar()}).catch(()=>{IDX={}});
window.slipHas=function(r,k){const m=MK[k];return !!(m&&IDX&&IDX[nm(r.name)+"|"+m[0]+"|"+m[1]])};
window.slipBtn=function(r,k){const m=MK[k];if(!m||!IDX)return"";const p=IDX[nm(r.name)+"|"+m[0]+"|"+m[1]];
 if(!p)return"";const key=p.aid+"|"+p.market,on=Q.includes(key);
 return`<button type="button" class="slbtn${on?" on":""}" data-slk="${key}" title="${on?"Remove from":"Add to"} bet slip">${on?"✓ In slip":"+ Slip"}</button>`};
function link(){return"https://betlab.sportslabshq.com/index.html#slip="+encodeURIComponent(Q.map(k=>"nhl~"+k).join(","))+"&add=1"}
function bar(){let b=document.getElementById("slbar");if(!b){b=document.createElement("div");b.id="slbar";document.body.appendChild(b)}
 b.hidden=!Q.length;if(!Q.length)return;
 b.innerHTML=`<a class="slbar-link" href="${link()}" target="_blank" rel="noopener"><span class="slbar-cnt">${Q.length}</span><span>in Slip · Open Bet Lab ↗</span></a><button type="button" class="slbar-clr" data-sl-clear="1" title="Clear slip" aria-label="Clear slip">✕</button>`}
document.addEventListener("click",e=>{
 const clr=e.target.closest("[data-sl-clear]");
 if(clr){e.preventDefault();e.stopPropagation();Q.length=0;save();document.querySelectorAll("[data-slk]").forEach(x=>{x.classList.remove("on");x.textContent="+ Slip"});return}
 const b=e.target.closest("[data-slk]");if(!b)return;e.preventDefault();e.stopPropagation();const k=b.dataset.slk,i=Q.indexOf(k);
 if(i>=0)Q.splice(i,1);else Q.push(k);save();document.querySelectorAll(`[data-slk="${k}"]`).forEach(x=>{const on=Q.includes(k);x.classList.toggle("on",on);x.textContent=on?"✓ In slip":"+ Slip"})},true);
const st=document.createElement("style");st.textContent=`.slbtn{font:700 11px/1.2 system-ui,sans-serif;padding:4px 9px;border-radius:99px;border:1px solid #3ddc97;background:#3ddc9718;color:#3ddc97;cursor:pointer;white-space:nowrap;transition:all .15s}.slbtn:hover{background:#3ddc9730}.slbtn.on{background:#3ddc97;color:#062016}#slbar{position:fixed;left:216px;bottom:12px;z-index:60;display:inline-flex;align-items:center;gap:6px;background:rgba(15,23,42,.95);backdrop-filter:blur(10px);border:1px solid rgba(61,220,151,.55);color:#e6ebff;font:700 11.5px/1 system-ui,sans-serif;padding:5px 8px 5px 6px;border-radius:99px;box-shadow:0 4px 16px rgba(0,0,0,.5)}#slbar[hidden]{display:none!important}.slbar-link{display:inline-flex;align-items:center;gap:6px;color:#e6ebff;text-decoration:none}.slbar-link:hover{color:#4fc3ff}.slbar-cnt{display:inline-flex;align-items:center;justify-content:center;background:#3ddc97;color:#062016;font-weight:800;font-size:10.5px;min-width:18px;height:18px;padding:0 5px;border-radius:99px}.slbar-clr{background:rgba(255,255,255,.08);border:0;color:#8d97b8;cursor:pointer;width:18px;height:18px;border-radius:50%;font-size:10px;display:inline-flex;align-items:center;justify-content:center;padding:0}.slbar-clr:hover{background:rgba(255,107,122,.25);color:#ff6b7a}@media(max-width:860px){#slbar{left:12px;bottom:12px}}`;document.head.appendChild(st);
document.readyState==="loading"?document.addEventListener("DOMContentLoaded",bar):bar();
})();
