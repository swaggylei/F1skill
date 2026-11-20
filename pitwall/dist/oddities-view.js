"use strict";
const oddIndex=findOddities(window.PITWALL_HISTORY.races,bookObservations);
const oddArticles={
 "2024-07-07":"https://www.formula1.com/en/latest/article/in-numbers-how-2024-came-to-be-one-of-the-most-thrilling-f1-seasons-yet.6nlrEsGGuIRTqA5TeFQHJ6",
 "2024-11-03":"https://www.formula1.com/en/latest/article/facts-and-stats-verstappen-breaks-schumacher-record-for-longest-stint-as.4JGyIPJdWP8RTZLVgNt3WO",
 "2023-09-03":"https://www.formula1.com/en/latest/article/in-numbers-the-remarkable-records-verstappen-and-red-bull-broke-in-2023.5rU6XbfSRwp1wH9Uzp4RxI"
};
let oddLimit=8;
function drawOddities(reset=true){
 if(reset)oddLimit=8;
 const mode=el("oddMode").value||"race",kind=el("oddKind").value;
 const modes=[["race","本站发现","This GP"],["watch","赛前可追","Before this GP"],["all","历届发现（截至本站）","History through this GP"]];
 el("oddMode").replaceChildren(...modes.map(([id,z,e])=>option(id,say(z,e))));el("oddMode").value=mode;
 el("oddKind").replaceChildren(option("",say("全部主题","All topics")),...Object.entries(oddKinds).map(([id,v])=>option(id,say(...v))));el("oddKind").value=kind;
 el("oddTitle").textContent=say("围场冷知识","Paddock curiosities");
 el("oddQuery").placeholder=say("搜索车手、分站或关键字","Search driver, race or keyword");
 el("oddMode").setAttribute("aria-label",say("查看范围","View"));
 el("oddKind").setAttribute("aria-label",say("冷门纪录主题","Record topic"));
 el("oddQuery").setAttribute("aria-label",el("oddQuery").placeholder);
 const query=el("oddQuery").value.trim().toLowerCase().replace(/斯托罗尔|斯特罗尔|斯托尔/g,"stroll").replace(/勒克莱尔|勒克莱奧/g,"leclerc");
 const matches=[];
 const start=mode==="all"?0:index;
 for(let j=index;j>=start;j--){
  const race=races[j];
  for(const rec of oddIndex[j][mode==="watch"?"watch":"results"]){
   if(kind && kind!==rec.kind)continue;
   if(query && ![race.name,race.year,rec.who,rec.zh,rec.en,...oddKinds[rec.kind]].join(" ").toLowerCase().includes(query))continue;
   matches.push({rec,race});
  }
 }
 el("oddScope").textContent=say("正赛名次与正赛排位 Q1 分开统计。","GP classification and GP qualifying Q1 are separate. ")+(mode==="watch"?say("按上一站结束时的数据推算。","Based on results through the preceding GP. "):say("按所选分站当时的历史比较。","Compared with the history available at that round. "))+say("共 "+matches.length+" 条。",matches.length+" matches.");
 const list=el("oddList");list.replaceChildren();
 for(const {rec,race} of matches.slice(0,oddLimit)){
  const box=node("details","");box.className="record";
  const summary=node("summary",say(...oddKinds[rec.kind])+" · "+rec.who);
  const body=node("p",en?rec.en:rec.zh);
  const refs=node("p",say("对照赛果　","Race references　"));
  for(const n of rec.refs){
   const ref=races[n],a=node("a",ref.year+" · "+ref.name);
   a.href="?gp="+ref.year+"-"+ref.round+(rec.kind.startsWith("q1")?"#qualifying":"#classification");refs.append(a);
  }
  if(rec.source){const a=node("a",rec.publisher||"TracingInsights");a.href=rec.source;refs.append(a);}
  if(rec.topic){const a=node("a",say("查看榜单与口径","View leaderboard"));a.href="almanac.html?topic="+encodeURIComponent(rec.topic);refs.append(a);}
  const source=node("a","F1DB "+release);source.href="https://github.com/f1db/f1db/releases/tag/"+release;refs.append(source);
  if(mode!=="watch" && oddArticles[race.date] && ["gap","grid","broken"].includes(rec.kind)){
   const official=node("a",say("F1 官方赛后资料","Formula 1 race notes"));official.href=oddArticles[race.date];refs.append(official);
  }
  box.append(summary,node("p",race.date+" · "+race.name),body,refs);
  if(matches.length===1 || (list.childElementCount===0 && mode!=="all"))box.open=true;
  list.append(box);
 }
 if(!matches.length){
  list.append(node("p",say("此范围没有匹配项。可查看历届发现或更换主题。","No matches. Try the historical view or another topic.")));
  if(mode==="race" && !kind && !query && index>0){
   const prior=races.slice(0,index).findLastIndex((_,i)=>oddIndex[i].results.length);
   if(prior>=0){
    const r=races[prior],link=node("a",say("上一次有发现的分站","Previous GP with a discovery")+" · "+r.date+" "+r.name);
    link.href="?gp="+r.year+"-"+r.round+"#odd";list.append(link);
   }
  }
 }
 el("oddMore").hidden=matches.length<=oddLimit;
 el("oddMore").textContent=say("再看 8 条","Show 8 more");
}
document.getElementById("oddMode").onchange=()=>drawOddities();
document.getElementById("oddKind").onchange=()=>drawOddities();
document.getElementById("oddQuery").oninput=()=>drawOddities();
document.getElementById("oddMore").onclick=()=>{oddLimit+=8;drawOddities(false);};
