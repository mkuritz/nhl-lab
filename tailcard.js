/* Sports Labs Universal 1-Tap Shareable Retina PNG Tail Card Generator (zero dependencies) */
(function(){
if(window.SLTailCard)return;

const css=`
#tail-mod{position:fixed;inset:0;z-index:9999;background:rgba(8,12,22,.86);backdrop-filter:blur(5px);display:none;align-items:center;justify-content:center;padding:16px}
#tail-mod.open{display:flex}
#tail-box{background:#121829;border:1px solid #26304f;border-radius:14px;padding:14px;max-width:680px;width:100%;text-align:center;color:#e8eefc;box-shadow:0 20px 60px rgba(0,0,0,.65);font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
#tail-box canvas{max-width:100%;height:auto;border-radius:10px;border:1px solid #26304f;display:block;margin:0 auto}
.sl-tail-btn{background:rgba(83,227,166,.1);border:1px solid rgba(83,227,166,.4);color:#53e3a6;border-radius:7px;padding:3px 8px;font:700 11px/1.25 system-ui,sans-serif;cursor:pointer;display:inline-flex;align-items:center;gap:4px;white-space:nowrap;text-decoration:none;transition:.12s}
.sl-tail-btn:hover{background:#53e3a6;color:#052010;border-color:#53e3a6}
.sl-bl-btn{background:rgba(56,189,248,.1);border:1px solid rgba(56,189,248,.4);color:#38bdf8;border-radius:7px;padding:3px 8px;font:700 11px/1.25 system-ui,sans-serif;cursor:pointer;display:inline-flex;align-items:center;gap:4px;white-space:nowrap;text-decoration:none;transition:.12s}
.sl-bl-btn:hover{background:#38bdf8;color:#061826;border-color:#38bdf8}
`;
if(!document.getElementById("sl-tailcard-css")){
 const st=document.createElement("style");st.id="sl-tailcard-css";st.textContent=css;document.head.appendChild(st);
}

function renderCanvas(opts){
 const hub=opts.hub||"SPORTS LABS";
 const title=String(opts.title||"Highlighted Insight");
 const sub=String(opts.sub||"Data → Action Research Card");
 const rows=opts.rows||[];
 const footerLeft=String(opts.footerLeft||"Sports Labs Quantitative Edge");
 const footerRight=String(opts.footerRight||"sportslabshq.com · 21+ Research Only");
 const acc=opts.accent||"#53e3a6";

 const W=680,rowH=64,Hpx=168+Math.max(1,rows.length)*rowH;
 const c=document.createElement("canvas");c.width=W*2;c.height=Hpx*2;
 const ctx=c.getContext("2d");ctx.scale(2,2);
 const g=ctx.createLinearGradient(0,0,W,Hpx);
 g.addColorStop(0,"#0b1120");g.addColorStop(1,"#131d36");
 ctx.fillStyle=g;ctx.fillRect(0,0,W,Hpx);
 ctx.fillStyle=acc;ctx.fillRect(0,0,W,4);
 ctx.fillStyle=acc;ctx.font="800 12px system-ui,sans-serif";
 ctx.fillText(`SPORTS LABS · ${hub.toUpperCase()} TAIL CARD`,24,28);
 ctx.fillStyle="#e8eefc";ctx.font="800 20.5px system-ui,sans-serif";
 ctx.fillText(title.slice(0,52),24,54);
 ctx.fillStyle="#8b97b0";ctx.font="600 12.5px system-ui,sans-serif";
 ctx.fillText(sub.slice(0,80),24,74);

 rows.forEach((r,i)=>{
  const y=92+i*rowH;
  ctx.fillStyle="#18223a";
  ctx.beginPath();
  if(ctx.roundRect)ctx.roundRect(20,y,W-40,rowH-8,8);
  else ctx.rect(20,y,W-40,rowH-8);
  ctx.fill();
  ctx.strokeStyle="#263354";ctx.lineWidth=1;ctx.stroke();

  const mainLbl=r.label||(r.player?`${r.player} · ${r.market||""}${r.line!=null?" o"+r.line:""}`:"Leg");
  ctx.fillStyle="#e8eefc";ctx.font="700 14.5px system-ui,sans-serif";
  ctx.fillText(String(mainLbl).slice(0,52),34,y+22);
  ctx.fillStyle="#94a3b8";ctx.font="600 12px system-ui,sans-serif";
  ctx.fillText(String(r.meta||"").slice(0,68),34,y+43);

  ctx.fillStyle=acc;ctx.font="800 14.5px system-ui,sans-serif";
  ctx.textAlign="right";ctx.fillText(String(r.rightTop||"").slice(0,30),W-34,y+22);
  ctx.fillStyle="#cbd5e1";ctx.font="600 11.5px system-ui,sans-serif";
  ctx.fillText(String(r.rightBot||"").slice(0,36),W-34,y+43);
  ctx.textAlign="left";
 });

 const fy=Hpx-24;
 ctx.fillStyle=acc;ctx.font="700 12.5px system-ui,sans-serif";
 ctx.fillText(footerLeft.slice(0,58),24,fy);
 ctx.fillStyle="#64748b";ctx.font="600 11.5px system-ui,sans-serif";
 ctx.textAlign="right";
 ctx.fillText(footerRight.slice(0,52),W-24,fy);
 ctx.textAlign="left";
 return c;
}

function openModal(canvas,filename){
 let m=document.getElementById("tail-mod");
 if(!m){
  m=document.createElement("div");m.id="tail-mod";
  m.innerHTML=`<div id="tail-box"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px"><b style="font-size:15px">📸 Shareable Tail Card</b><button type="button" id="tail-cls" style="background:none;border:0;color:#e8eefc;font-size:18px;cursor:pointer">✕</button></div><div id="tail-cv"></div><div style="display:flex;gap:8px;justify-content:center;margin-top:10px"><button type="button" id="tail-dl" style="background:#53e3a6;color:#052010;border:0;border-radius:8px;padding:7px 14px;font-weight:800;cursor:pointer">⬇ Download PNG</button><button type="button" id="tail-cp" style="background:#182033;color:#e8eefc;border:1px solid #26304f;border-radius:8px;padding:7px 14px;font-weight:700;cursor:pointer">📋 Copy Image</button></div></div>`;
  document.body.appendChild(m);
  m.onclick=e=>{if(e.target===m||e.target.id==="tail-cls")m.classList.remove("open")};
 }
 const holder=document.getElementById("tail-cv");holder.innerHTML="";holder.appendChild(canvas);
 const cpBtn=document.getElementById("tail-cp");if(cpBtn)cpBtn.textContent="📋 Copy Image";
 document.getElementById("tail-dl").onclick=()=>{const a=document.createElement("a");a.download=filename||"sportslabs-tailcard.png";a.href=canvas.toDataURL("image/png");a.click()};
 document.getElementById("tail-cp").onclick=()=>{canvas.toBlob(b=>{try{navigator.clipboard.write([new ClipboardItem({"image/png":b})]);document.getElementById("tail-cp").textContent="✓ Copied!"}catch(e){}})};
 m.classList.add("open");
}

function show(opts){
 const cv=renderCanvas(opts);
 openModal(cv,opts.filename||"sportslabs-tailcard.png");
 return cv;
}

window.SLTailCard={renderCanvas,openModal,show};
})();
