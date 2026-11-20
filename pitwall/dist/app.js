"use strict";
const {events, rules,coverage} = window.PITWALL;
const $ = id => document.getElementById(id);
const esc = value => String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const names = Object.fromEntries(events.flatMap(e=>e.results.map(r=>[r.driver_id,r.driver_name||r.driver_id])));
const places={"Bahrain Grand Prix":"巴林大奖赛","Saudi Arabian Grand Prix":"沙特阿拉伯大奖赛"};
const categories={"NEW RECORDS":"新纪录与追平","BROKEN RECORDS":"打破纪录","ENDED STREAKS":"连续纪录终结","STILL ACTIVE":"延续中的纪录","WEIRD & INTERESTING":"趣味观察","HISTORICAL CONTEXT":"历史背景"};
const aliases={zhou_guanyu:"周冠宇",guanyu_zhou:"周冠宇",max_verstappen:"维斯塔潘",sergio_perez:"佩雷兹",red_bull:"红牛",ferrari:"法拉利",charles_leclerc:"勒克莱尔",carlos_sainz:"塞恩斯"};
let en=false, pre=true, selected=events.length-1;
const t=(zh,eng)=>en?eng:zh;
const nice=id=>id.split("+").map(x=>names[x]||x.replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase())).join(" · ");
const raceName=e=>en?e.name:(places[e.name]||e.name);
const podium=e=>e.results.filter(r=>[1,2,3].includes(r.position)).sort((a,b)=>a.position-b.position);
function links(sources){
 return sources.filter(s=>s.url.startsWith("https://")).map(s=>'<a href="'+esc(s.url)+'" target="_blank" rel="noopener noreferrer">'+esc(s.title)+'</a>').join("");
}
function card(label,title,body){return '<article class="card"><small>'+esc(label)+'</small><strong>'+esc(title)+'</strong><p>'+esc(body)+'</p></article>';}
function lookout(history,result){
 if(!history.length)return '<p class="blank">'+t("这是样本首站，尚无上一站数据可用于赛前比较。","This is the opening round of the sample. No prior GP is available for comparison.")+'</p>';
 const previous=podium(history.at(-1)), [first,second]=previous, actual=result?podium(result):[];
 const streak=fn=>{let n=0;for(const e of [...history].reverse()){if(!fn(podium(e)))break;n++;}return n;};
 const oneTwo=p=>p[0].constructor_id===first.constructor_id&&p[1].constructor_id===first.constructor_id;
 const ids=p=>p.map(r=>r.driver_id).sort().join("+");
 const checks=[
 [t("车手 · 连胜","DRIVER · WIN STREAK"),nice(first.driver_id),t("再胜一场，样本内连胜将达","Another win extends the in-scope streak to ")+(streak(p=>p[0].driver_id===first.driver_id)+1)+t(" 场。"," GPs."),actual[0]?.driver_id===first.driver_id],
 [t("车队 · 前二席位","TEAM · ONE–TWO"),nice(first.constructor_id),oneTwo(previous)?t("再次包揽前二，连续场数将达","Another one–two extends the streak to ")+(streak(oneTwo)+1)+t(" 场。"," GPs."):t("这支上站冠军车队能否包揽前二？","Can the previous winning constructor finish one–two?"),result&&oneTwo(actual)],
 [t("组合 · 领奖台","COMBINATION · PODIUM"),previous.map(r=>nice(r.driver_id).split(" ").at(-1)).join(" / "),t("若三人再次登台，这一组合在范围内将出现","If all three return, the in-scope trio count reaches ")+(history.filter(e=>ids(podium(e))===ids(previous)).length+1)+t(" 次，不限顺序。"," regardless of order."),result&&ids(previous)===ids(actual)]
 ];
 return checks.map(([label,title,body,hit])=>card(label+(result?(hit?t("  /  已达成","  /  MET"):t("  /  未达成","  /  MISSED")):""),title,body)).join("");
}
function draw(){
 document.documentElement.lang=en?"en":"zh-CN";
 const event=events[selected], before=events.slice(0,selected), history=pre?before:events.slice(0,selected+1), last=history.at(-1);
 const topic=$("topic").value;
 $("race").innerHTML=events.map((e,i)=>'<option value="'+i+'">'+e.season+' · R'+String(e.round).padStart(2,"0")+'　'+esc(raceName(e))+'</option>').join("");
 $("race").value=selected;
 const labels={navArchive:t("历史档案","Archive"),navExplore:t("查纪录","Records"),navSources:t("来源","Sources"),lang:en?"中文":"EN",raceLabel:t("比赛周","Weekend"),pre:t("赛前看点","Pre-race"),post:t("赛后回放","Post-race"),edition:t("历史回放","HISTORICAL REPLAY")+"   /   ROUND "+String(event.round).padStart(2,"0"),headline:raceName(event),subtitle:en?"Formula 1 record book":event.name,heroDate:event.date+"　 /　"+t("正赛","Grand Prix"),watchTitle:pre?t("本周末看什么","Weekend watchlist"):t("赛前看点兑现了吗？","Watchlist results"),watchCut:t("比较基线","Baseline")+" · "+(before.at(-1)?.date||"—"),exploreTitle:t("纪录检索","Record explorer"),scope:t("可查询正赛","Available GPs")+" · "+history.length,sourcesTitle:t("统计范围与来源","Scope and sources"),graphicLabel:last?(pre?t("上一站领奖台","PREVIOUS PODIUM"):t("本站领奖台","RACE PODIUM"))+"  /  "+last.date:t("赛前基线","PRE-RACE BASELINE")};
 for(const [id,text] of Object.entries(labels))$(id).textContent=text;
 $("pre").setAttribute("aria-pressed",String(pre));$("post").setAttribute("aria-pressed",String(!pre));
 $("query").placeholder=t("搜索车手、车队或纪录，如「领奖台」「Red Bull」","Search drivers, teams or records, e.g. podium");
 $("query").setAttribute("aria-label",$("query").placeholder);
 $("topic").setAttribute("aria-label",t("纪录类别","Record category"));
 $("topic").innerHTML='<option value="">'+t("全部类别","All categories")+'</option>'+Object.entries(categories).map(([k,v])=>'<option value="'+k+'">'+t(v,k)+'</option>').join("");
 $("topic").value=topic;
 $("podium").innerHTML=last?'<div class="steps">'+[1,0,2].map(i=>{const r=podium(last)[i];return '<div class="step p'+r.position+'"><strong>P'+r.position+'</strong><span>'+esc(nice(r.driver_id).split(" ").at(-1))+'</span></div>';}).join("")+'</div>':'<p>'+t("首站尚无历史席位","No preceding podium in scope")+'</p>';
 $("cards").innerHTML=lookout(before,pre?null:event);
 $("limits").textContent=t("历史快照，仅覆盖所选视角下的已导入正赛。所有展示均标记为 provisional（待复核）。发车位取实际发车顺位，组合不区分登台次序。","Historical snapshot covering the imported GPs up to this view. All web observations are provisional. Grid means starting position. Podium trios are unordered.")+" "+(history.length?history[0].date+" — "+last.date:"");
 $("links").innerHTML=history.map(e=>'<details><summary>'+esc(raceName(e))+' · '+esc(e.date)+'</summary>'+links(e.sources)+'<p>'+t("资料获取日期","Source retrieval date")+' · '+esc(e.sources[0].retrieved_at.slice(0,10))+'</p></details>').join("");
 drawList(history);
 showSelections(en);
}
function drawList(history){
 const search=$("query").value.trim().toLowerCase(), category=$("topic").value;
 const items=[];
 for(const event of [...history].reverse()){
   const gains=event.results.filter(r=>r.finished&&r.position&&r.grid>r.position);
   const max=Math.max(...gains.map(r=>r.grid-r.position));
   const extra=gains.filter(r=>r.grid-r.position===max).map(r=>({rule_id:"gain",category:"WEIRD & INTERESTING",entities:[r.driver_id],before:"P"+r.grid,after:"P"+r.position,unit:t("本站有可比发车位的完赛车手中提升最多","largest gain among finishers with known grids")}));
   const background={rule_id:"context",category:"HISTORICAL CONTEXT",entities:[],before:null,after:event.date,unit:t("正赛 · 范围起点 "+history[0].date,"GP · coverage starts "+history[0].date)};
   for(const c of [...extra,...event.claims,background]){
    const rule=rules[c.rule_id]|| (c.rule_id==="gain"?{zh:"本站名次跃升",en:"Race positions gained"}:{zh:"历史比较范围",en:"Comparison period"});
    const who=c.entities.map(nice).join(" / "), title=t(rule.zh,rule.en);
    const terms=[who,title,rule.zh,rule.en,c.category,categories[c.category],raceName(event),event.name,...c.entities.flatMap(id=>id.split("+").map(x=>aliases[x]||x))].join(" ").toLowerCase();
    if((category&&category!==c.category)||(search&&!terms.includes(search)))continue;
    items.push('<details class="record"><summary>'+esc(title)+' · '+esc(who||raceName(event))+'<b>'+esc(c.before??"—")+' → '+esc(c.after)+'</b></summary><p>'+esc(t(categories[c.category],c.category))+' · '+esc(c.unit)+(c.tied?t(" · 并列"," · tied"):"")+'</p><p class="status">'+esc(event.date)+' · GP · PROVISIONAL</p>'+links(event.sources)+'</details>');
   }
 }
 $("list").innerHTML=items.join("")||'<p class="blank">'+t("当前范围没有匹配的纪录。可切换比赛周、关键词或类别。","No matching records in scope. Change the race, search or category.")+'</p>';
}
$("race").onchange=e=>{selected=Number(e.target.value);draw();};
$("pre").onclick=()=>{pre=true;draw();};$("post").onclick=()=>{pre=false;draw();};
$("lang").onclick=()=>{en=!en;draw();};
const filter=()=>drawList(events.slice(0,selected+(pre?0:1)));
$("query").oninput=filter;$("topic").onchange=filter;
draw();
