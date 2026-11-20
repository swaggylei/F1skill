"use strict";
const {races,release}=window.PITWALL_HISTORY;
const records=findOddities(races,bookObservations);
const years=[...new Set(races.map(r=>r.year))].reverse();
const el=id=>document.getElementById(id);
const make=(tag,text)=>Object.assign(document.createElement(tag),{textContent:text});
const addOption=(id,value,text)=>el(id).append(new Option(text,value));
const size=10;
let english=false,page=0;
const tr=(zh,en)=>english?en:zh;
function controls(year,kind,order){
 for(const id of ["year","kind","order"])el(id).replaceChildren();
 addOption("year","all",tr("全部赛季","All seasons"));
 for(const y of years)addOption("year",y,y);
 addOption("kind","all",tr("所有纪录","All records"));
 addOption("kind","qualifying",tr("Q1 序列（含终结）","Q1 runs, including endings"));
 for(const [key,label] of Object.entries(oddKinds))addOption("kind",key,tr(...label));
 addOption("order","asc",tr("从早到晚","Oldest first"));addOption("order","desc",tr("从晚到早","Newest first"));
 el("year").value=year;el("kind").value=kind;el("order").value=order;
 for(const [id,zh,en] of [["year","赛季","Season"],["kind","纪录类型","Record type"],["query","车手或分站","Driver or GP"],["order","排序","Sort order"]])el(id).setAttribute("aria-label",tr(zh,en));
 document.documentElement.lang=english?"en":"zh-CN";
 const labels={title:tr("逐站冷门纪录","Race-by-race curiosities"),intro:tr("沿赛历看每一站留下了什么，也可以跟着一位车手读完一段连续纪录。","Follow the championship calendar or trace one driver’s run across races."),archive:tr("历史档案","Archive"),lang:english?"中文":"EN",stroll:tr("看 Stroll 连续止步 Q1","Trace Stroll’s Q1 exits"),leclerc:tr("看 Leclerc 第四名账本","Trace Leclerc’s P4 finishes"),reset:tr("恢复赛季视图","Reset season view"),prev:tr("上一页","Previous"),next:tr("下一页","Next"),methodTitle:tr("统计口径与来源","Definitions and data source"),method:tr("正赛第四按最终分类逐人逐站计，同站只计一次。Q1 仅覆盖 2017–2026 常规淘汰制的大奖赛排位。须有有效 Q1 圈速、无 Q2/Q3 圈速且落在晋级线外（严格更快者达到晋级名额）。连续三站起展示，中断须有晋级证据才标作终结。缺席、未知、无有效圈或无覆盖会断开序列。冲刺排位不计。数据来自 F1DB，尚未逐场复核 FIA 裁定。","P4 uses final GP classifications, once per driver per race. Q1 covers standard knockout GP qualifying in 2017–2026. We require a valid Q1 lap, no Q2/Q3 time and enough strictly faster Q1 laps to place the driver outside the cut. Runs appear from three rounds. Only evidenced advancement marks an end. Absences, unknowns and coverage gaps interrupt the count. Sprint qualifying is excluded. Individual FIA decisions await review.")};
 for(const [id,value] of Object.entries(labels))el(id).textContent=value;
 el("query").placeholder=tr("搜索车手、分站或关键词","Search driver, GP or keyword");
 el("source").href="https://github.com/f1db/f1db/releases/tag/"+release;el("source").textContent="F1DB "+release;
}
function render(){
 const year=el("year").value,kind=el("kind").value;
 const query=el("query").value.trim().toLowerCase().replace(/斯托罗尔|斯特罗尔|斯托尔/g,"stroll").replace(/勒克莱尔/g,"leclerc");
 const groups=[];
 for(const [i,r] of races.entries()){
  if(year!=="all"&&Number(year)!==r.year)continue;
  const items=records[i].results.filter(c=>(kind==="all"||kind===c.kind||(kind==="qualifying"&&c.kind.startsWith("q1")))&&[c.who,c.zh,c.en,r.name,...oddKinds[c.kind]].join(" ").toLowerCase().includes(query));
  if(items.length || (kind==="all"&&!query))groups.push({r,items});
 }
 if(el("order").value==="desc")groups.reverse();
 page=Math.min(page,Math.max(0,Math.ceil(groups.length/size)-1));
 const start=page*size,visible=groups.slice(start,start+size);
 el("count").textContent=groups.length?tr("共 "+groups.length+" 站，当前第 "+(start+1)+"–"+(start+visible.length)+" 站。",groups.length+" rounds · showing "+(start+1)+"–"+(start+visible.length)):tr("没有匹配的纪录。","No matching records.");
 el("prev").disabled=!page;el("next").disabled=start+size>=groups.length;
 el("feed").replaceChildren();
 for(const {r,items} of visible){
  const section=make("article","");section.className="round";
  const heading=make("h2",""),link=make("a",r.date+" · R"+r.round+" · "+r.name);
  link.href="archive.html?gp="+r.year+"-"+r.round+"#odd";heading.append(link);section.append(heading);
  if(!items.length)section.append(make("p",tr("本站没有触发已收录的纪录规则。","No tracked record triggered at this round.")));
  for(const c of items){
   const box=make("details",""),text=english?c.en:c.zh;
   box.append(make("summary",c.who+" · "+text));
   const status=c.kind==="feature"?tr("官方文章记载","Formula 1 report"):c.kind==="almanac"?tr("历史榜单快照","Published snapshot"):"provisional";
   box.append(make("p",tr(...oddKinds[c.kind])+" · "+(c.session||(c.kind.startsWith("q1")?"GP QUALIFYING":"GP RACE"))+" · "+status));
   if(c.source){const a=make("a",c.publisher||"TracingInsights");a.href=c.source;box.append(a);}
   if(c.topic){const a=make("a",tr("查看榜单与口径","View leaderboard"));a.href="almanac.html?topic="+encodeURIComponent(c.topic);box.append(a);}
   for(const j of c.refs){
    const ref=races[j],a=make("a",ref.year+" R"+ref.round+" · "+ref.name);
    a.href="archive.html?gp="+ref.year+"-"+ref.round+(c.kind.startsWith("q1")?"#qualifying":"#classification");box.append(a);
   }
   section.append(box);
  }
  el("feed").append(section);
 }
}
function filter(){page=0;render();}
function preset(kind,name){el("year").value="all";el("kind").value=kind;el("query").value=name;el("order").value="asc";filter();}
el("stroll").onclick=()=>preset("qualifying","Stroll");el("leclerc").onclick=()=>preset("p4","Leclerc");
el("reset").onclick=()=>{controls(years[0],"all","asc");el("query").value="";filter();};
el("lang").onclick=()=>{english=!english;controls(el("year").value,el("kind").value,el("order").value);render();};
for(const id of ["year","kind","order"])el(id).onchange=filter;
el("query").oninput=filter;
function turn(delta){page+=delta;render();el("count").scrollIntoView({block:"start"});}
el("prev").onclick=()=>turn(-1);el("next").onclick=()=>turn(1);
controls(years[0],"all","asc");
const presetName=new URLSearchParams(location.search).get("driver");
if(presetName==="stroll")preset("qualifying","Stroll");
else if(presetName==="leclerc")preset("p4","Leclerc");
else render();
