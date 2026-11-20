"use strict";

// Editorial archive. Dates refer to the races themselves, not publication dates.
const pitwallSelections = [
 {
  gp:"1954-5", place:["1954 英国站","1954 British GP"],
  title:["一个最快圈积分，七个人平分","One fastest-lap point, divided seven ways"],
  body:["在 Silverstone，Stirling Moss、Juan Manuel Fangio 等七人并列跑出正赛最快圈。按当年的积分规则，每人拿到 1/7 分。看这场的积分表时，小数点后藏着另外六个和他一样快的人。","Seven drivers, including Stirling Moss and Juan Manuel Fangio, tied for the fastest race lap at Silverstone. The scoring rules split the single bonus point equally. Each driver's share was exactly one seventh."],
  sources:[["最快圈积分规则","Fastest-lap scoring","https://www.formula1.com/en/latest/article/bonus-point-to-be-awarded-for-fastest-lap-in-2019.4gwBT6QW1NR1AlrlzAkKSP.html"]]
 },
 {
  gp:"1971-9", place:["1971 意大利站","1971 Italian GP"],
  title:["冠军冲线后 0.61 秒，第五名也到了","First to fifth in 0.61 seconds"],
  body:["Peter Gethin 在 Monza 先于 Ronnie Peterson 0.01 秒冲线。再往成绩表下面看，连第五名 Howden Ganley 距冠军也只有 0.61 秒。两个差值都以冠军的完赛时间为基准。","Peter Gethin beat Ronnie Peterson by 0.01 seconds at Monza. Read down to fifth and Howden Ganley was only 0.61 seconds behind Gethin. Both gaps are measured from the winner."],
  sources:[["官方完赛时间差","Official finishing gaps","https://www.formula1.com/en/results/1971/races/299/italy/race-result"]]
 },
 {
  gp:"1982-14", place:["1982 瑞士站","1982 Swiss GP"],
  title:["世界冠军的唯一一胜，在法国的瑞士站","A champion’s only win came at the Swiss GP in France"],
  body:["Keke Rosberg 的 1982 年车手世界冠军赛季只有一场正赛胜利。赛事名称是瑞士大奖赛，比赛却在法国 Dijon-Prenois 举行。赛季收官时，他以 44 分位列第一。","Keke Rosberg won one Grand Prix in his 1982 title season. It was the Swiss Grand Prix, held across the border at Dijon-Prenois in France. He finished the season first on 44 points."],
  sources:[["赛季回顾","Season retrospective","https://www.formula1.com/en/latest/article/from-glory-with-one-race-win-to-triumphing-by-a-single-point-the-most.5IoDGAcUM682cRO3DcruN7"],["车手积分榜","Drivers’ standings","https://www.formula1.com/en/results/1982/drivers"]]
 },
 {
  gp:"2005-4", place:["2005 圣马力诺站","2005 San Marino GP"],
  title:["等了近八年的第二个领奖台，在赛后才到手","A second podium nearly eight years later, awarded after the race"],
  body:["Alexander Wurz 上一次登台还是 1997 年英国站。2005 年在 Imola，他替受伤的 Juan Pablo Montoya 出赛。原列第三的 Jenson Button 被取消成绩，Wurz 在最终分类中升至第三，两次领奖台之间相隔 2,842 天。","Alexander Wurz had last taken a podium at the 1997 British GP. At Imola in 2005 he stood in for the injured Juan Pablo Montoya. Jenson Button’s disqualification from third promoted Wurz to the podium, 2,842 days after his first."],
  sources:[["最终分类与取消成绩说明","Classification and disqualifications","https://www.formula1.com/en/results/2005/races/774/san-marino/race-result"],["两次领奖台的间隔","Podium intervals","https://www.formula1.com/en/latest/article/schumachers-comeback-and-wurzs-record-wait-10-of-the-longest-gaps-between-f1.5JyntGTCalj6SWrERQvrO0"]]
 },
 {
  gp:"2007-10", place:["2007 欧洲站","2007 European GP"],
  title:["一生只跑一场 F1 正赛，却领跑了六圈","One career start, six laps in the lead"],
  body:["Markus Winkelhock 驾驶 Spyker 在 Nürburgring 排位垫底。起步前他押了雨胎，大雨随后落下。翻到最终成绩表，只看得见他退赛。他却在这唯一一次出赛中领跑了六圈。","Markus Winkelhock qualified last for Spyker at the Nürburgring. He chose wet tyres before the start and the rain arrived. His final result shows a retirement. The lap leaders tell the other half of the story: six laps in front on his only Grand Prix start."],
  sources:[["轮胎选择与领跑圈数","Tyre choice and laps led","https://www.formula1.com/en/latest/article/like-father-like-son-the-second-generation-f1-racers.198AIj4fZRvDApe0WFbMnq"],["当场重启录像","Race restart footage","https://www.formula1.com/en/video/nuerburgring-2007-when-markus-winkelhock-led-a-grand-prix.1687507295365046965"]]
 }
];

function showSelections(english) {
 const lang=Number(english);
 const section=document.getElementById("picks");
 const heading=document.createElement("h2");
 heading.textContent=english?"Curator’s picks from F1 history":"编辑精选 · F1 历史里的怪纪录";
 const grid=document.createElement("div");
 grid.className="selection-grid";
 for(const story of pitwallSelections){
  const article=document.createElement("article");
  const race=document.createElement("a");
  race.href="archive.html?gp="+story.gp+"#classification";
  race.textContent=story.place[lang];
  const title=document.createElement("h3");
  title.textContent=story.title[lang];
  const body=document.createElement("p");
  body.textContent=story.body[lang];
  article.append(race,title,body);
  for(const source of story.sources){
   const link=document.createElement("a");
   link.href=source[2];
   link.textContent="Formula 1 · "+source[lang];
   article.append(link);
  }
  grid.append(article);
 }
 section.replaceChildren(heading,grid);
}
