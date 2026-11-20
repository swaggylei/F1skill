"use strict";
const bookDomains={
 championships:"总冠军",chassis:"底盘",circuits:"赛道","driver-of-the-day":"全场最佳",drivers:"车手","fastest-laps":"最快圈","first-rows":"头排",
 "gp-entries":"参赛经历","grands-prix":"大奖赛",h2h:"队友交锋",laps:"圈数与节奏",lead:"赛道位置",milestones:"里程碑",misc:"生涯奇闻",
 numbers:"车号",penalties:"处罚","pit-stops":"进站",podiums:"领奖台",points:"积分",poles:"杆位",practice:"练习赛",qualifying:"排位赛",
 races:"比赛过程",seasons:"赛历与旅行",sprints:"冲刺赛",streaks:"连续纪录",tyres:"轮胎",wins:"胜利"
};
const bookUnits={
 "1st Lap DNFs":"首圈退赛次数","2nd Places":"亚军次数","3rd Places":"季军次数",Age:"年龄（岁）","Average Gap (%)":"平均差距（%）","Average age":"平均年龄（岁）","Avg Gap (s)":"平均差距（秒）",Awards:"获奖次数","Best Position":"最佳名次",Circuits:"赛道数",DNFs:"退赛次数",DNQs:"未通过排位次数",DSQs:"取消资格次数",Deciders:"决出冠军次数",Deployments:"部署次数",Drivers:"车手数",Engines:"引擎数","Fastest Laps":"最快圈次数",Finish:"完赛名次",Finishers:"获分类人数",Finishes:"次数","First Rows":"头排次数",GPs:"大奖赛数","Gap (ms)":"差距（毫秒）","Grand Slams":"大满贯次数",Grid:"发车位","Grid Position":"发车位","Hat Tricks":"帽子戏法次数",Km:"公里",km:"公里","km/h":"公里/时",Laps:"圈数",Lockouts:"包揽次数","Margin (%)":"差距（%）","Margin (s)":"差距（秒）",Nations:"国籍数",Penalties:"处罚次数",Periods:"阶段数","Pit-Lane Time (s)":"通过维修区用时（秒）","Place Changes":"名次变化数",Places:"位置数","Places Gained":"上升位数","Places Lost":"下降位数",Podiums:"领奖台次数",Points:"积分","Pole Sitters":"杆位车手数",Poles:"杆位次数",Polesitters:"杆位车手数",Position:"名次",Positions:"名次数","Positions Gained":"上升位数",Races:"场次","Races (%)":"分站比例（%）","Rate %":"比例（%）","Rate (%)":"比例（%）","Red Flags":"红旗次数",Retirements:"退赛次数",Seasons:"赛季数",Seconds:"秒",Sessions:"节数",Starts:"起跑次数",Stops:"进站次数",Streak:"连续场数",Teams:"车队数","Time (ms)":"用时（毫秒）",Times:"次数","Times 2nd":"年度亚军次数",Titles:"总冠军数","Vote Share (%)":"得票率（%）",Weekends:"比赛周末数",Winners:"不同冠军数",Wins:"胜场",Year:"年份",Years:"年"
};
const bookSource=topic=>"https://tracinginsights.com/stats/records/"+topic.key;
// Each date is the race date. The linked article may be a later retrospective.
const curiositiesArticle="https://www.formula1.com/en/latest/article/from-a-qualifying-dead-heat-to-the-lowest-ever-finish-12-of-f1s-weirdest-and.7xNY7kgbMdw2mJZcgCLeey";
const raceFeatures=[
 ["1992-11","1992-08-16","Hungary","Damon Hill / Graham Hill","父子各自最后一次为 Brabham 出赛，都拿了第十一。父亲在 1972 年的 Watkins Glen，儿子在二十年后的匈牙利。","Damon finished P11 on his last outing for Brabham in Hungary. His father Graham had signed off for the same team in P11 at Watkins Glen twenty years earlier.","GP RACE",curiositiesArticle],
 ["1997-17","1997-10-26","Europe · Jerez","Jacques Villeneuve / Michael Schumacher / Heinz-Harald Frentzen","赫雷斯排位赛，三人的最快圈全是 1:21.072。Villeneuve 最先做出这个时间，拿到杆位。","All three set a best qualifying lap of 1:21.072 at Jerez. Villeneuve earned pole by recording the time first.","GP QUALIFYING",curiositiesArticle],
 ["2011-8","2011-06-26","Europe · Valencia","Narain Karthikeyan","瓦伦西亚的 24 辆赛车全部看到方格旗。Karthikeyan 开着 HRT，拿到一个通常连出现在成绩表上都很难的名次：第 24 名。","All 24 starters reached the flag at Valencia. Karthikeyan brought the HRT home in an unusually crowded final position, P24.","GP RACE",curiositiesArticle],
 ["2022-10","2022-07-03","Great Britain","Carlos Sainz / Max Verstappen","连续两站，冠军都在个人第 150 次正赛起跑时从杆位取胜。上一站加拿大是 Verstappen，这一站银石换成 Sainz，也是他的首胜。","Two successive races went to pole-sitters making their 150th Grand Prix start. Verstappen won in Canada, then Sainz took his maiden win at Silverstone.","GP RACE","https://www.formula1.com/en/latest/article/facts-and-stats-hamilton-sets-new-podium-record-as-sainz-becomes-spains.4sXuykEfkg4YBDtS83cVoi"],
 ["2023-2","2023-03-19","Saudi Arabia","Fernando Alonso","Alonso 第一个跑完吉达的首圈。他上一次以领跑者身份完成大奖赛第一圈，还要追溯到 2012 年德国站。","Alonso crossed the line first at the end of lap one in Jeddah. His previous opening-lap lead had come at the 2012 German GP.","GP RACE","https://www.formula1.com/en/latest/article/facts-and-stats-perez-leads-a-red-bull-1-2-for-the-very-first-time.5qUXwV8dh8ajgbZ1irDu9h"],
 ["2024-8","2024-05-26","Monaco","Charles Leclerc","连续 12 次拿到杆位却没能赢下那一场之后，Leclerc 在家乡把杆位变成了冠军。这里数的是他自己的杆位机会。","Leclerc won his home race from pole after 12 successive personal pole positions had failed to yield a win. The sequence counts his own poles.","GP RACE","https://www.formula1.com/en/latest/article/facts-and-stats-first-monegasque-winner-in-monaco-since-1931-as-leclerc.4iQxLmf1Hz5i9OLxtuXdDt"],
 ["2025-15","2025-08-31","Netherlands","Oscar Piastri / Mika Häkkinen","Piastri 在赞德沃特拿杆位、赢正赛、跑最快圈，还领跑了每一圈。上一次 McLaren 车手集齐这四项，是 Häkkinen 在 1998 年摩纳哥。","Piastri took pole, the win and fastest lap, leading every lap at Zandvoort. McLaren’s previous such sweep was Häkkinen’s at Monaco in 1998.","GP WEEKEND","https://www.formula1.com/en/latest/article/facts-and-stats-piastri-equals-manager-webbers-f1-win-total-with-dutch-grand.4m2Me7bfjhMG85evYkvQez"]
].map(([gp,date,race,who,zh,en,session,source])=>({gp,date,race,who,zh,en,session,source,kind:"feature",publisher:"Formula 1",refs:[]}));
const bookObservations=new Map();
for(const item of raceFeatures){
 if(!bookObservations.has(item.gp))bookObservations.set(item.gp,[]);
 bookObservations.get(item.gp).push(item);
}
for(const t of window.PITWALL_BOOK){
 for(const e of t.entries){
  if(!e.gp)continue;
  const domain=t.key.split("/")[0];
  const session=({sprints:"SPRINT",poles:"GP QUALIFYING",penalties:"STEWARDS","fastest-laps":"GP FASTEST LAP",seasons:"CALENDAR",misc:"GP WEEKEND"})[domain]||"GP RACE";
  const estimated=e.context.includes("(est.)");
  const c={kind:"almanac",who:e.name,zh:"本站数据 · "+(bookUnits[t.unit]||t.unit)+" "+e.value+(estimated?"（估算）":"")+"（收录于「"+t.zh+"」）",
   en:"Race value · "+t.unit+" "+e.value+(estimated?" (estimated)":"")+" (table: "+t.en+")",session,refs:[],topic:t.key,source:bookSource(t)};
  if(!bookObservations.has(e.gp))bookObservations.set(e.gp,[]);
  bookObservations.get(e.gp).push(c);
 }
}
