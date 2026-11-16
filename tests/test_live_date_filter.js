// Pure date-filter helpers mirrored from live-analyzer.js (America/New_York midnight rollover, same as the Daily Slate).
function etTodayFrom(ms){return new Date(ms).toLocaleDateString('en-CA',{timeZone:'America/New_York'})}
function fmtDay(d){return new Date(d+'T12:00').toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric'})}
function shiftDate(d,n){const x=new Date(d+'T12:00');x.setDate(x.getDate()+n);const y=x.getFullYear(),m=String(x.getMonth()+1).padStart(2,'0'),day=String(x.getDate()).padStart(2,'0');return y+'-'+m+'-'+day}
function relLabel(d,td){const x=(new Date(d+'T12:00')-new Date(td+'T12:00'))/864e5;return x===-1?'Yesterday':x===0?'Today':x===1?'Tomorrow':fmtDay(d)}
function latestStage(G){const order=['p1','p2','reg','final'];let s=null;for(const k of order) if(G&&G.stages&&G.stages[k]) s=k;return s}
function gamesOn(idx, date){return Object.values(idx.games||{}).filter(g=>g.date===date)}

let failed=0;
function eq(name, a, b){const ok=JSON.stringify(a)===JSON.stringify(b);if(!ok){failed++;console.error('FAIL',name,a,'!=',b)}else console.log('ok',name)}

// Nov 15, 2026 10:30 PM ET = Nov 16 03:30Z; still "today" Nov 15 (midnight ET rollover).
eq('et today evening', etTodayFrom(Date.parse('2026-11-16T03:30:00Z')), '2026-11-15');
// Nov 16, 2026 12:30 AM ET = Nov 16 05:30Z; rolls to Nov 16.
eq('et today after midnight', etTodayFrom(Date.parse('2026-11-16T05:30:00Z')), '2026-11-16');
eq('shift yesterday', shiftDate('2026-11-15',-1), '2026-11-14');
eq('shift tomorrow', shiftDate('2026-11-15',1), '2026-11-16');
eq('label yesterday', relLabel('2026-11-14','2026-11-15'), 'Yesterday');
eq('label today', relLabel('2026-11-15','2026-11-15'), 'Today');
eq('label tomorrow', relLabel('2026-11-16','2026-11-15'), 'Tomorrow');
eq('fmt Sat Nov 14', fmtDay('2026-11-14'), 'Sat, Nov 14');
eq('latest is final, not p2', latestStage({stages:{p1:{},p2:{},reg:{},final:{}}}), 'final');
eq('latest p2 when no later board', latestStage({stages:{p1:{},p2:{}}}), 'p2');

const idx={games:{
  '2026020323':{gid:2026020323,date:'2026-11-14'},
  '2026020326':{gid:2026020326,date:'2026-11-15'},
  '2026020327':{gid:2026020327,date:'2026-11-15'}
}};
eq('default today hides yesterday', gamesOn(idx,'2026-11-15').map(g=>g.gid).sort(), [2026020326,2026020327]);
eq('yesterday only', gamesOn(idx,'2026-11-14').map(g=>g.gid), [2026020323]);

function startKey(g){const m=String(g.start||'').match(/(\d{1,2}):(\d{2})\s*(AM|PM)/i);if(!m)return 9e4+g.gid;let h=+m[1]%12;if(/pm/i.test(m[3]))h+=12;return h*60+ +m[2]}
const ordered=[{gid:1,start:'10:00 PM'},{gid:2,start:'3:30 PM'},{gid:3,start:'1:00 PM'}].sort((a,b)=>startKey(a)-startKey(b)||a.gid-b.gid).map(g=>g.start)
eq('start sort afternoon then late', ordered, ['1:00 PM','3:30 PM','10:00 PM']);

if(failed){console.error(failed,'failed');process.exit(1)}
console.log('all passed');
