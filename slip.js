/* NHL Lab -> Bet Lab shared slip. Picks map to Bet Lab's NHL props (same keys), then open in Bet Lab's slip. */
(function(){
const LS="nhllab:slip",MK={pG:["Anytime Goal",.5],pP:["Points",.5],p3S:["Shots on Goal",2.5]};
const nm=s=>String(s||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z]/g,"");
let IDX=null,Q=[];try{Q=JSON.parse(localStorage.getItem(LS)||"[]")}catch(e){}
const save=()=>{localStorage.setItem(LS,JSON.stringify(Q));bar()};
fetch("https://betlab.sportslabshq.com/data/props_nhl.json?t="+Date.now()).then(r=>r.ok?r.json():[]).then(d=>{IDX={};(d||[]).forEach(p=>{IDX[nm(p.player)+"|"+p.market+"|"+p.line]=p});if(window.route)route();bar()}).catch(()=>{IDX={}});
window.slipBtn=function(r,k){const m=MK[k];if(!m||!IDX)return"";const p=IDX[nm(r.name)+"|"+m[0]+"|"+m[1]];
 if(!p)return`<div class="small m" style="margin-top:4px">No line yet</div>`;const key=p.aid+"|"+p.market,on=Q.includes(key);
 return`<button type="button" class="slbtn${on?" on":""}" data-slk="${key}" title="${on?"Remove from":"Add to"} bet slip">${on?"✓ In slip":"+ Add to bet slip"}</button>`};
function link(){return"https://betlab.sportslabshq.com/index.html#slip="+encodeURIComponent(Q.map(k=>"nhl~"+k).join(","))+"&add=1"}
function bar(){let b=document.getElementById("slbar");if(!b){b=document.createElement("a");b.id="slbar";b.target="_blank";b.rel="noopener";document.body.appendChild(b)}
 b.hidden=!Q.length;b.href=link();b.innerHTML=`🧾 ${Q.length} pick${Q.length==1?"":"s"} · Open bet slip in Bet Lab ›`}
document.addEventListener("click",e=>{const b=e.target.closest("[data-slk]");if(!b)return;e.preventDefault();e.stopPropagation();const k=b.dataset.slk,i=Q.indexOf(k);
 if(i>=0)Q.splice(i,1);else Q.push(k);save();document.querySelectorAll(`[data-slk="${k}"]`).forEach(x=>{const on=Q.includes(k);x.classList.toggle("on",on);x.textContent=on?"✓ In slip":"+ Add to bet slip"})},true);
const st=document.createElement("style");st.textContent=`.slbtn{margin-top:6px;font:700 11.5px system-ui,sans-serif;padding:4px 9px;border-radius:99px;border:1px solid #53e3a6;background:#53e3a614;color:#53e3a6;cursor:pointer;white-space:nowrap}.slbtn.on{background:#53e3a6;color:#0b1220}#slbar{position:fixed;right:14px;bottom:44px;z-index:60;background:#53e3a6;color:#0b1220;font:800 13px system-ui,sans-serif;padding:10px 14px;border-radius:99px;text-decoration:none;box-shadow:0 6px 20px #0008}#slbar[hidden]{display:none}@media(max-width:600px){#slbar{left:12px;right:12px;text-align:center;bottom:52px}}`;document.head.appendChild(st);
document.readyState==="loading"?document.addEventListener("DOMContentLoaded",bar):bar();
})();
