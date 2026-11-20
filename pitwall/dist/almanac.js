"use strict";
const get=id=>document.getElementById(id);
const make=(tag,text)=>Object.assign(document.createElement(tag),{textContent:text});
const link=(label,url)=>Object.assign(make("a",label),{href:url});
const topics=window.PITWALL_BOOK;
let en=false,page=0;
const size=12;
const tr=(zh,eng)=>en?eng:zh;
const notes={
 "races/lap-one-changes":["将所有完成首圈的车手升降名次的绝对值相加。两辆车互换位置，就会产生两份名次变化。","Adds each lap-one finisher’s absolute position change. Two drivers swapping places contribute two changes."],
 "grands-prix/gap-most":["被套圈时，原榜可能以估算秒差表示。精确冲线差距应以原表标注为准。","The source may estimate a time gap for a lapped runner-up. Check each row for that qualification."],
 "pit-stops/winner-most-stops":["2011 加拿大站，Jenson Button 六次驶入维修区，最后依然夺冠。六次之中包含一次通过维修区处罚。原榜从 1994 年有进站数据的比赛开始统计。","Button won in Canada in 2011 after six pit-lane visits, including a drive-through penalty. The table covers races with pit-stop data from 1994 onward.","https://www.formula1.com/en/latest/article/canada-2011-torrential-rain-a-safety-car-record-and-buttons-charge-the.1ZWPateMlCFLZ8U6KQBNXj"],
 "podiums/same-order-trio":["交换冠军和亚军，这个组合就另算一次。普通的三人同台统计会把两种次序合并。","Swapping the winner and runner-up creates a different trio here. Unordered podium counts combine both arrangements."],
 "poles/did-not-start":["例如 2021 Monaco，Charles Leclerc 拿到杆位，赛车却没能参加正赛起跑。","At Monaco in 2021, Charles Leclerc held pole but his car did not start the race.","https://www.formula1.com/en/latest/article/in-numbers-how-well-do-drivers-perform-at-their-home-race-and-who-might-become-a-first-time-home-winner-in-2026.2mHNaj0RuyivAggRduAiLf"],
 "misc/grand-slams":["拿杆位、赢正赛、跑最快圈，还要每一圈都是领跑者。F1 官方记录的 2022 Imola 就是一例。","Pole, victory, fastest lap and the lead on every lap. Verstappen completed the set at Imola in 2022.","https://www.formula1.com/en/latest/article/facts-and-stats-a-grand-slam-first-and-red-bulls-maiden-double-score-at.7nAGUuihqzKZA9PoyCUCf6"],
 "poles/pole-without-win":["Chris Amon 的五个杆位始终没换来一场正赛胜利。","Chris Amon took five poles across a career without a Grand Prix victory.","https://www.formula1.com/en/latest/article/unlucky-for-some-13-of-f1s-most-unfortunate-records.2MgJsNRazBTqQdZdoVuWZM"]
};
function settings(){
 const selected=get("domain").value;
 get("domain").replaceChildren(new Option(tr("全部主题","All subjects"),""));
 for(const domain of [...new Set(topics.map(t=>t.key.split("/")[0]))])get("domain").append(new Option(tr(bookDomains[domain],domain),domain));
 get("domain").value=selected;
 document.documentElement.lang=en?"en":"zh-CN";
 const n=topics.reduce((s,t)=>s+t.entries.length,0);
 for(const [id,text] of Object.entries({title:tr("冷门纪录馆","The F1 record almanac"),timeline:tr("逐站时间线","Race timeline"),lang:tr("EN","中文"),clear:tr("清除筛选","Reset"),prev:tr("上一页","Previous"),next:tr("下一页","Next"),
 intro:tr(`${topics.length} 种统计口径，${n.toLocaleString()} 条榜单实例。资料截至 2026 圣保罗站。`,`${topics.length} distinct measures and ${n.toLocaleString()} entries through São Paulo 2026.`),
 creditText:tr("来源：TracingInsights 根据 F1DB 编制的开放榜单。Pitwall 选题、翻译标题与单位、节选各表前十行，并关联可定位的分站。数据截止 2026-11-08，在线原榜可能已更新。","Open rankings compiled by TracingInsights from F1DB. Pitwall selected topics, translated labels and units, excerpted the first ten rows and linked identifiable races. Snapshot through 2026-11-08. Online tables may have changed.")}))get(id).textContent=text;
 get("query").placeholder=tr("试试「生日」「安全车」「队友」或车手英文名","Search birthday, safety car or a driver");
 get("query").setAttribute("aria-label",get("query").placeholder);get("domain").setAttribute("aria-label",tr("主题分类","Subject"));
}
function render(){
 const normalize=text=>text.normalize("NFD").replace(/\p{M}/gu,"").toLowerCase();
 const term=normalize(get("query").value.trim()),domain=get("domain").value;
 const matching=topics.filter(t=>(!domain||t.key.startsWith(domain+"/"))&&normalize([t.zh,t.en,t.key,...t.entries.flatMap(e=>[e.name,e.context])].join(" ")).includes(term));
 const stories=domain?[]:raceFeatures.filter(s=>normalize([s.date,s.race,s.who,s.zh,s.en].join(" ")).includes(term));
 get("stories").hidden=!stories.length;get("storiesList").replaceChildren();
 get("storyHeading").textContent=tr("分站故事 · Formula 1 史料","Race stories from Formula 1");
 for(const s of stories){
  const p=make("p","");p.append(link(s.date+" · "+s.race,"archive.html?gp="+s.gp+"#odd"),"　"+tr(s.zh,s.en)+" ",link(tr("官方原文","Formula 1 article"),s.source));
  get("storiesList").append(p);
 }
 page=Math.max(0,Math.min(page,Math.ceil(matching.length/size)-1));
 get("count").textContent=matching.length?tr(`共 ${matching.length} 个口径 · 第 ${page+1} / ${Math.ceil(matching.length/size)} 页`,`${matching.length} measures · Page ${page+1} of ${Math.ceil(matching.length/size)}`):tr("没有匹配的榜单。","No matching leaderboards.");
 get("prev").disabled=!page;get("next").disabled=(page+1)*size>=matching.length;
 const container=get("cardsBook");container.replaceChildren();
 for(const t of matching.slice(page*size,page*size+size)){
  const cat=t.key.split("/")[0],unit=tr(bookUnits[t.unit]||t.unit,t.unit);
  const box=make("article","");box.className="entry";box.id=t.key;
  box.append(make("small",tr(bookDomains[cat],cat)),make("h2",tr(t.zh,t.en)));
  const first=t.entries[0];box.append(make("p",first.name+" · "+first.value+" ("+unit+")"+(first.context?" · "+first.context:"")));
  const note=notes[t.key];if(note){const p=make("p",tr(note[0],note[1]));if(note[2])p.append(" ",link("Formula 1",note[2]));box.append(p);}
  const details=make("details",""),list=make("ul","");
  details.append(make("summary",tr("查看口径及 "+t.entries.length+" 条实例","Definition and "+t.entries.length+" entries")),make("p",t.definition));
  if(t.coverage)details.append(make("p",tr("原表覆盖说明 · ","Coverage · ")+t.coverage));
  for(const e of t.entries){
   const row=make("li","#"+e.rank+"　"+e.name+" · "+e.value+" ("+unit+")"+(e.context?" · "+e.context:""));
   const extra=Object.entries(e).filter(([k,v])=>!["rank","name","value","context","url","gp"].includes(k)&&v);
   if(extra.length)row.append(make("small","　"+extra.map(([k,v])=>k.replaceAll("_"," ")+" "+v).join(" · ")));
   if(e.gp)row.append(" ",link(tr("分站档案","Race archive"),"archive.html?gp="+e.gp+"#odd"));
   list.append(row);
  }
  details.append(list,link(tr("原榜、并列项与完整名单","Source leaderboard, ties and full list"),bookSource(t)));
  box.append(details);container.append(box);
 }
}
get("lang").onclick=()=>{en=!en;settings();render();};
get("domain").onchange=get("query").oninput=()=>{page=0;render();};
get("clear").onclick=()=>{get("query").value="";get("domain").value="";page=0;render();};
for(const [id,step] of [["prev",-1],["next",1]])get(id).onclick=()=>{page+=step;render();get("count").scrollIntoView();};
settings();
const selectedKey=new URLSearchParams(location.search).get("topic");
if(topics.some(t=>t.key===selectedKey))get("query").value=selectedKey;
render();
