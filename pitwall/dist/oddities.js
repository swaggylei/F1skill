"use strict";

// Each item is tied to its discovery round. Pre-race items read prior state only.
function findOddities(races, publishedRecords = new Map()) {
 const lastWin = new Map(), trios = new Map(), streaks = new Map();
 const winningGrids = [];
 const fourths = new Map(), fourthsSeason = new Map(), previousPlace = new Map(), q1Streak = new Map();
 const preWinSeconds=new Map(), scorelessElevenths=new Map();
 let longest = 0, recordRace = null, previousTrio = null;
 return races.map((race, i) => {
  const watch = [], results = [];
  function item(list, kind, who, zh, en, refs) {
   list.push({kind, who, zh, en, refs:[...new Set(refs)]});
  }
  for (const s of streaks.values()) {
   if (s.n >= 3) item(watch,"active",s.name,
    `已连赢 ${s.n} 场。如果本站再胜，连续正赛胜场将达 ${s.n+1}。`,
    `On ${s.n} straight GP wins. Another victory would make it ${s.n+1}.`,[s.start,i-1]);
  }
  if (previousTrio) {
   const p = previousTrio;
   item(watch,"trio",p.names,`若上站三人再登台，将是这个组合第 ${p.n+1} 次同台，名次顺序不限。`,
    `If the previous podium reunites, it will be appearance ${p.n+1} for this unordered trio.`,[p.first,i-1]);
  }
  for (const [id,run] of q1Streak) {
   if (run.count>=3) item(watch,"q1",run.name,`此前连续 ${run.count} 站止步 Q1。若本周正赛排位再度止步 Q1，将达到 ${run.count+1} 站。`,
    `A further Q1 exit in GP qualifying would extend this ${run.count}-round run to ${run.count+1}.`,[run.first,i-1]);
   if(race.q1?.[id]==="out")continue;
   if(run.count>=3 && race.q1?.[id]==="advanced")item(results,"q1end",run.name,
    `连续 ${run.count} 站止步 Q1 后，本站进入下一节。可核验序列从 ${races[run.first].date} 开始，当前归零。`,
    `Advanced after ${run.count} consecutive evidenced Q1 exits, counted from ${races[run.first].date}. The active count resets to zero.`,[run.first,i-1,i]);
   q1Streak.delete(id);
  }
  for(const [id,status] of Object.entries(race.q1||{})){
   if(status!=="out")continue;
   const name=race.rows.find(r=>r[8]===id)?.[1]||id;
   const run=q1Streak.get(id)||{first:i,count:0,name};
   run.count++;q1Streak.set(id,run);
   if(run.count>=3)item(results,"q1",name,`正赛排位连续止步 Q1：${run.count-1} → ${run.count} 站。起点 ${races[run.first].date}，按日历跨赛季累计。`,
    `Consecutive evidenced GP qualifying Q1 exits: ${run.count-1} → ${run.count}, from ${races[run.first].date}, across seasons.`,[run.first,i]);
  }
  const ranks=new Map();
  for(const row of race.rows){
   if(!/^\d+$/.test(row[0]))continue;
   const id=row[8],place=Number(row[0]);
   if(!ranks.has(id)||place<Number(ranks.get(id)[0]))ranks.set(id,row);
  }
  for(const row of race.rows.filter(r=>r[0]==="4").filter((r,n,rows)=>rows.findIndex(other=>other[8]===r[8])===n)){
   const id=row[8],key=race.year+"/"+id,prev=fourths.get(id)||{count:0,last:null};
   const season=(fourthsSeason.get(key)||0)+1;
   item(results,"p4",row[1],`正赛最终列第四，生涯 P4 场次 ${prev.count} → ${prev.count+1}，其中本赛季 ${season} 次。按车手逐站计数。`,
    `Classified fourth: career P4 appearances ${prev.count} → ${prev.count+1}, including ${season} this season. Each GP counts once per driver.`,
    prev.last===null?[i]:[prev.last,i]);
   fourths.set(id,{count:prev.count+1,last:i});fourthsSeason.set(key,season);
  }
  for(const [id,row] of ranks){
   const pos=Number(row[0]),prev=previousPlace.get(id);
   if(pos===2 && !lastWin.has(id)){
    const seconds=preWinSeconds.get(id)||[];
    seconds.push(i);preWinSeconds.set(id,seconds);
    if(seconds.length>=3)item(results,"runnerup",row[1],`尚未赢过正赛，已经第 ${seconds.length} 次获得亚军（此前 ${seconds.length-1} 次）。`,
     `Still awaiting a first GP win after career second place number ${seconds.length}, up from ${seconds.length-1}.`,[seconds[0],seconds.at(-2),i]);
   }
   if(race.year>=2010 && pos===11 && row[5]!=="" && Number(row[5])===0){
    const key=race.year+"/"+id,elevenths=scorelessElevenths.get(key)||[];
    elevenths.push(i);scorelessElevenths.set(key,elevenths);
    if(elevenths.length>=3)item(results,"p11",row[1],`本赛季第 ${elevenths.length} 次正赛列第十一且本站得零分，此前已有 ${elevenths.length-1} 次。`,
     `Season count of P11 classifications with zero GP points: ${elevenths.length-1} → ${elevenths.length}.`,[elevenths[0],elevenths.at(-2),i]);
   }
   const start=prev?.pos===pos && prev.last===i-1?prev.start:i;
   const count=i-start+1;
   if(pos>=2 && pos<=11 && count>=3)item(results,"repeat",row[1],
    `连续 ${count} 场正赛都列 P${pos}（此前 ${count-1} 场）。按日历相邻分站和每站个人最佳正式名次统计。`,
    `Classified P${pos} at ${count} consecutive GPs, up from ${count-1}. Uses each driver's best classified place per calendar round.`,[start,i]);
   previousPlace.set(id,{pos,start,last:i});
  }
  const podium = race.rows.filter(r=>["1","2","3"].includes(r[0]));
  const winners = new Map(podium.filter(r=>r[0]==="1").map(r=>[r[8],r]));
  for (const [id,s] of streaks) {
   if (winners.has(id)) continue;
   if (s.n >= 3) item(results,"ended",s.name,`${s.n} 场连胜在本站终结。当前连胜归零，原来的连续成绩仍保留。`,
    `The ${s.n}-GP winning streak ends here. The active count resets to zero.`,[s.start,i-1,i]);
   streaks.delete(id);
  }
  if (winners.size > 1) item(results,"shared",[...winners.values()].map(r=>r[1]).join(" / "),
   `一场正赛，${winners.size} 位车手获第一名。该站在大奖赛总数中只计一次。`,
   `One GP credited first place to ${winners.size} drivers. It counts once on the championship calendar.`,[i]);
  for (const [id,row] of winners) {
   const s=streaks.get(id)||{name:row[1],start:i,n:0};
   s.n++; streaks.set(id,s);
   const old=lastWin.get(id);
   if (old!==undefined) {
    const days=(Date.parse(race.date)-Date.parse(races[old].date))/86400000;
    if (days>=365) item(results,"gap",row[1],`两场胜利相隔 ${days} 天，中间举行了 ${i-old-1} 场正赛（含缺席的分站）。`,
     `${days} days between successive victories, with ${i-old-1} championship GPs in between, including absences.`,[old,i]);
   }
   lastWin.set(id,i);
   const grid=Number(row[3]);
   if (winners.size===1 && Number.isInteger(grid) && grid>0) {
    if (grid>=10) {
     const comparable=winningGrids.filter(previous=>previous.grid>=grid);
     item(results,"grid",row[1],
      `从 P${grid} 发车夺冠。此前 ${winningGrids.length} 场可比正赛中，仅 ${comparable.length} 场的冠军从 P${grid} 或更后发车。仅比较发车位已知、独享胜利的分站。`,
      `Won from P${grid}. Of ${winningGrids.length} previous GPs with one winner and a numeric grid, ${comparable.length} were won from P${grid} or further back.`,
      [...comparable.slice(-2).map(previous=>previous.i),i]);
    }
    winningGrids.push({grid,i});
   }
  }
  const peak=Math.max(...[...streaks.values()].map(s=>s.n));
  if (peak>=3 && peak>=longest) {
   const leaders=[...streaks.values()].filter(s=>s.n===peak);
   item(results,peak===longest?"tie":"broken",leaders.map(s=>s.name).join(" / "),
    `档案内最长车手连胜：${longest} → ${peak} 场。${peak===longest?"本站追平原最高值。":"本站刷新最高值。"}`,
    `Longest driver GP win streak in the archive: ${longest} → ${peak}. ${peak===longest?"Existing mark equalled.":"New high."}`,
    [recordRace,...leaders.map(s=>s.start),i].filter(n=>n!==null));
  }
  if (peak>longest) {longest=peak;recordRace=i;}
  previousTrio=null;
  if (podium.length===3 && new Set(podium.map(r=>r[0])).size===3 && new Set(podium.map(r=>r[8])).size===3) {
   const key=podium.map(r=>r[8]).sort().join("|");
   const p=trios.get(key)||{n:0,first:i,last:i,names:podium.map(r=>r[1]).join(" / ")};
   p.n++;
   if (p.n>=2) item(results,"trio",p.names,`这三人第 ${p.n} 次同台（赛前 ${p.n-1} 次）。上一次是 ${races[p.last].date}，不要求名次相同。`,
    `Unordered podium appearances: ${p.n-1} → ${p.n}. Previous occurrence on ${races[p.last].date}.`,[p.first,p.last,i]);
   p.last=i; trios.set(key,p);previousTrio=p;
   const ordered=[...podium].sort((a,b)=>Number(a[0])-Number(b[0]));
   const grids=ordered.map(r=>Number(r[3]));
   if (grids.every(n=>Number.isInteger(n)&&n>0) && grids[0]>grids[1] && grids[1]>grids[2])
    item(results,"reverse",ordered.map(r=>r[1]).join(" / "),`领奖台三人从 P${grids.join("、P")} 发车，最终依次获前三。他们之间的相对次序完全颠倒。`,
     `The podium finishers started P${grids.join(", P")} respectively. Their relative order was completely reversed.`,[i]);
  }
  const published=publishedRecords.get(race.year+"-"+race.round)||[];
  return {watch,results:[...published,...results]};
 });
}

const oddKinds={
 almanac:["来源榜单选录","Published record tables"], feature:["赛后史料","Race notes"],
 runnerup:["首胜之前的亚军","Runner-up before a first win"],p11:["反复列第十一且零分","Repeated scoreless P11s"],
 q1:["连续止步 Q1","Q1 exit streak"],q1end:["告别 Q1 淘汰","Q1 streak ended"],p4:["第四名账本","P4 finishes"],repeat:["连续相同名次","Same-place streak"],
 grid:["低位发车夺冠","Deep-grid wins"],gap:["久违的胜利","Gaps between wins"],trio:["领奖台重聚","Podium reunions"],
 reverse:["前三逆序","Reversed podium order"],shared:["共享胜利","Shared wins"],active:["连胜追踪","Active streaks"],
 ended:["连胜终结","Ended streaks"],tie:["追平最长连胜","Longest streak equalled"],broken:["刷新最长连胜","Longest streak surpassed"]
};
