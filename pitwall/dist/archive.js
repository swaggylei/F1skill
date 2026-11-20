"use strict";
const {races,release}=window.PITWALL_HISTORY;
const el=id=>document.getElementById(id);
let en=false, index=races.length-1;
const requested=new URLSearchParams(location.search).get("gp");
const requestedIndex=races.findIndex(r=>r.year+"-"+r.round===requested);
if(requestedIndex>=0)index=requestedIndex;
const say=(zh,eng)=>en?eng:zh;
const years=[...new Set(races.map(r=>r.year))].reverse();
const option=(value,label)=>new Option(label,value);
const node=(tag,value)=>Object.assign(document.createElement(tag),{textContent:value});
function rank(){
 const totals=new Map();
 const wins=el("metric").value==="wins";
 for(const r of races.slice(0,index)){
   const credited=new Set();
   for(const [pos,name,,,,,,,id] of r.rows){
     if(!(wins?pos==="1":["1","2","3"].includes(pos))||credited.has(id))continue;
     credited.add(id);
     const current=totals.get(id)||{name,count:0};
     current.count++;
     totals.set(id,current);
   }
 }
 const q=el("filter").value.trim().toLowerCase();
 const matches=[...totals.values()].filter(d=>d.name.toLowerCase().includes(q))
   .sort((a,b)=>b.count-a.count||a.name.localeCompare(b.name));
 el("rankRows").replaceChildren(...matches.slice(0,20).map(d=>node("li",d.name+" · "+d.count)));
 if(!matches.length)el("rankRows").append(node("li",say("没有符合条件的既往成绩","No prior matching results")));
}
function render(){
 const r=races[index], metric=el("metric").value||"wins";
 document.documentElement.lang=en?"en":"zh-CN";
 const labels={home:say("赛事回放","Race replay"),lang:en?"中文":"EN",title:say("世界锦标赛正赛档案","Championship race archive"),
 totals:races[0].date+" — "+races.at(-1).date+"　/　"+years.length+say(" 个赛季"," seasons")+"　/　"+races.length+say(" 场正赛"," GPs"),
 seasonLabel:say("赛季","Season"),raceLabel:say("分站","Round"),name:r.name,date:r.date,circuit:r.circuit,rankTitle:say("本站开赛前的车手纪录","Driver records before this GP"),
 explain:say("从 1950 年累计到本站上一场。共享成绩按获该名次的车手计，每位车手每站最多计一次。显示匹配结果前 20 位。","Counts from 1950 through the preceding GP. Shared places credit each driver, at most once per GP. Showing the first 20 matches."),
 sourceTitle:say("数据来源与口径","Sources and scope"),note:say("正赛成绩由 F1DB 整理，本站选取并重排字段。保留共享赛车、原始排名和缺失值。历史档案尚未逐场复核 FIA 裁定。","Race results compiled by F1DB. Pitwall selects and reformats fields and retains shared entries, source positions and missing values. Individual FIA decisions await review.")};
 for(const [id,value] of Object.entries(labels))el(id).textContent=value;
 el("metric").replaceChildren(option("wins",say("正赛胜场","GP wins")),option("podiums",say("正赛领奖台场次","GP podium races")));
 el("metric").value=metric;el("metric").setAttribute("aria-label",say("统计项目","Statistic"));
 el("filter").placeholder=say("输入车手英文名","Search driver name");el("filter").setAttribute("aria-label",el("filter").placeholder);
 el("season").replaceChildren(...years.map(y=>option(y,y)));el("season").value=r.year;
 el("gp").replaceChildren(...races.flatMap((race,i)=>race.year===r.year?[option(i,"R"+race.round+" · "+race.name)]:[]));el("gp").value=index;
 const hdr=document.createElement("tr");
 for(const h of (en?["Pos.","Driver","Constructor","Grid","Laps","Points","Notes"]:["名次","车手","制造商","发车位","圈数","积分","备注"]))hdr.append(node("th",h));
 el("head").replaceChildren(hdr);
 el("rows").replaceChildren(...r.rows.map(([pos,driver,team,grid,laps,points,shared,reason])=>{
  const tr=document.createElement("tr");
  for(const value of [pos,driver,team,grid,laps,points,[shared?say("共享赛车","Shared car"):"",reason].filter(Boolean).join(" · ")])tr.append(node("td",value||"—"));
  return tr;
 }));
 el("release").textContent="F1DB "+release;el("release").href="https://github.com/f1db/f1db/releases/tag/"+release;
 el("official").href="https://www.formula1.com/en/results/"+r.year+"/races";
 el("qTitle").textContent=say("正赛排位 · 可核验的 Q1 淘汰","GP qualifying · evidenced Q1 exits");
 const eliminated=Object.entries(r.q1||{}).filter(([,status])=>status==="out").map(([id])=>r.rows.find(row=>row[8]===id)?.[1]||id);
 el("qInfo").textContent=r.q1?eliminated.join(" · ")||say("无可判定项","No evidenced exits"):say("此站无覆盖","No coverage for this round");
 if(location.hash==="#qualifying")el("qualifying").open=true;
 rank();
 drawOddities();
 showSelections(en);
}
el("season").onchange=e=>{index=races.findIndex(r=>r.year===Number(e.target.value));render();};
el("gp").onchange=e=>{index=Number(e.target.value);render();};
el("metric").onchange=rank;el("filter").oninput=rank;
el("lang").onclick=()=>{en=!en;render();};
render();
