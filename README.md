# F1 Knowledge Skill 🏁

通用、可迁移的 F1 知识 Skill：历史、车手、车队，以及每场大奖赛后有证据可查的冷门纪录追踪。

A portable, evidence-led Formula 1 skill for history, drivers, constructors and unusual post-race records. Chinese and English supported; race reports default to Chinese with English proper names.

## Pitwall 网页 / Web record book

在[冷门纪录馆](pitwall/dist/almanac.html)可以搜「生日」「首圈」「队友」或车手英文名。每种口径列出原榜前十行以内的实例、原文统计定义、覆盖说明（如有）和完整榜单链接。能精确定位的单场表现同时出现在逐站时间线。Formula 1 官方文章整理的分站故事附原文链接，生涯总数按快照截止日展示。

榜单快照截至 2026-11-08，选自 [TracingInsights 开放统计](https://tracinginsights.com/stats/data)，底层为 [F1DB v2026.20.0](https://github.com/f1db/f1db/releases/tag/v2026.20.0)，以 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 署名。选题及译名在 `pitwall/record-topics.tsv`。在仓库根目录用 `python pitwall/import_almanac.py records.zip f1db-csv.zip` 重建本版。程序核对两个发布包的 SHA-256；引入新版时需先审阅原榜口径、覆盖日期与校验值。榜单更新与下文历史赛果同步独立。

从 [逐站冷门纪录](pitwall/dist/timeline.html) 按赛季与时间顺序浏览，也可以直接追踪 Stroll 的 Q1 淘汰序列或 Leclerc 的正赛 P4 次数。时间线区分累计次数、连续场数和序列终结。Q1 使用 F1DB 的大奖赛排位分段数据，覆盖 2017–2026 年可判定的常规淘汰制场次。缺失或无法判定的场次中断可核验序列。运行下方历史档案更新脚本时，会一并更新分段数据。

从首页「历史档案」进入 [世界锦标赛正赛档案](pitwall/dist/archive.html)，可离线查阅自 1950 年起各站赛果及本站开赛前的车手胜场、登台场次。数据由 [F1DB](https://github.com/f1db/f1db) 提供，按 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 署名使用。本站从发布包选取、重排字段并计算累计次数。页面标明数据版本和已收录的最后一场比赛。

要同步历史档案，在仓库根目录运行 `python pitwall/history.py`。程序获取最新稳定版、核对 SHA-256，再替换离线数据。更新后重新发布 `pitwall/dist/` 即可。网页只纳入已有正赛成绩的世界锦标赛分站。

The full GP archive includes shared drives and preserves missing data. The separate two-race replay below demonstrates the evidence-review workflow.

历史档案的「围场冷知识」可以切换本站发现、赛前可追和截至本站的历届发现。发车位第十或更后夺冠、两胜相隔至少 365 天、三连胜及以上的终结、领奖台组合重聚等条目由正赛数据生成。展开条目可回看依据分站。更新 F1DB 快照后会自动重新计算。

下载仓库后，在浏览器打开 [Pitwall 首页](pitwall/dist/index.html)。默认以 2024 沙特站赛前为视角，展示巴林站后的已知数据。切到赛后可查看三项看点是否达成，并按车手、车队、纪录主题或类别检索。截至所选站的来源和统计范围可以展开查阅。支持中英文切换与离线阅读。

The bundled replay covers Bahrain and Saudi Arabia 2024. To update the website after a tracker sync, run `python pitwall/build.py path/to/tracker.sqlite3` from the repository root, then serve or publish the whole `pitwall/dist/` folder. A normalized JSON snapshot is also accepted. Running the command without a path rebuilds the two-race demo. Web results are provisional observations. The site reads a local snapshot on page load.

## 使用 / Usage

将 [`f1-knowledge/`](f1-knowledge/SKILL.md) 整个目录复制到支持 Markdown Skill 的平台技能目录。若平台没有 Skill 发现机制，把 SKILL.md 作为任务指令加载，并让它能够读取 references。无需专有插件或第三方 Python 依赖；追踪需要联网检索和可持久化的文件目录。

Copy the whole `f1-knowledge/` folder into your host's skill directory, or load SKILL.md as instructions with access to its references. Tracking requires browsing and writable persistent storage. Configure `F1_KNOWLEDGE_DATA_DIR` or use `./f1-knowledge-data`.

示例 / Examples:

```text
使用 f1-knowledge，检查自上次执行以来已结束的大奖赛，逐场生成赛后纪录报告。
Use f1-knowledge to explain unusual driver records, with definitions and sources.
用中英文对照解释车队更名与 constructor 纪录统计的区别。
Audit pending provisional claims and revise affected reports.
```

首次运行默认建立基线并处理最近一个已结束大奖赛；需要补历史时指定起始日期。运行数据和报告由执行平台保存在数据目录，迁移时一起复制。不附带未经核验的“当前纪录数据库”。

On first run, establish a dated baseline and process the latest completed GP. Specify a start date for historical catch-up. Copy runtime data with the skill when migrating. No unverified current-record database is bundled.

## 追踪机制 / Tracking

每次执行核对已结束的 GP、待补赛事与 provisional 项；区分正赛、Sprint、排位、杆位及最快圈。报告包括 NEW RECORDS、BROKEN RECORDS、ENDED STREAKS、WEIRD & INTERESTING、STILL ACTIVE、HISTORICAL CONTEXT。无新 GP 时不例行通知；实质更正与访问失败分别标记处理。来源不足则披露缺口。

The portable Markdown skill now includes an optional Python tracker in this repository. The tracker provides 20 deterministic GP metrics, SQLite revision history, JSON/Markdown reports and a local notification outbox. It requires Python 3.10+ on Linux/macOS, with no third-party packages. A host scheduler must invoke it for recurring checks; no background service or external notifications are enabled by installation. A suitable recurring task prompt for the broader research skill is:

> Run f1-knowledge in tracking mode. Check completed GPs since stored state, process backlog chronologically and review provisional claims. Persist reports and provenance. Suppress routine notification if no new GP; emit material corrections or operational errors only as specified by the skill.

详细规则见 [Skill](f1-knowledge/SKILL.md)、[统计定义](f1-knowledge/references/definitions.md)、[状态协议](f1-knowledge/references/state.md)。官方入口：[FIA](https://www.fia.com/documents)、[Formula1.com](https://www.formula1.com/en/results)；历史交叉核验：[STATS F1](https://www.statsf1.com/en/statistiques.aspx)。具体报告必须引用具体文件，入口链接本身不证明纪录。

## 第一版计算程序 / Tracker v0.1

**v0.2 更新：** 新增官方赛果对照、2024 范围内基线检查、FIA 文件清单和最终成绩 PDF 检查、独立复核记录，以及逐条纪录的核验状态。相同数据再次同步保留复核结论；相关事实变化时自动标为过期。详见 [证据核验指南](f1-knowledge/references/verification.md)。自动对照一致记为 `matched`，不会自动断言处罚或申诉已经核清。

从仓库根目录运行。演示数据全部为虚构测试数据，使用独立目录，不能作为真实赛事报告发送：

```bash
python3 -m f1tracker --data-dir /tmp/f1skill-demo import examples/synthetic-season.json --backfill
python3 -m f1tracker --data-dir /tmp/f1skill-demo status
python3 -m f1tracker --data-dir /tmp/f1skill-demo outbox
```

真实数据同步示例（需要环境允许 `api.jolpi.ca`；年份必须明确，可根据任务调整）：

```bash
python3 -m f1tracker --data-dir ./f1-knowledge-data sync --start-year 2023 --end-year 2024
```

首次运行只报告最新 GP，较早赛事用于建立基线；`--backfill` 才生成范围内所有历史报告。相同输入重复执行不会重复通知，无变化时标准输出为空。失败返回非零退出码并记录运行日志。同步会重新核对整个选定范围，捕获数据修订。

**范围和证据限制：** v0.1 支持 2000 年以来、从首站开始且连续的 GP 赛果快照；不包括 Sprint、排位、杆位、最快圈或早期共享驾驶。20 条规则的纪录只对声明的导入范围有效。Jolpica 属于二手来源，自动同步产生的报告始终标为 `provisional`，不会宣称已完成 FIA 核验或发现全历史纪录。数据访问失败不能算作“无新赛事”。2024 整季真实 API 同步与重复运行已验证；v0.2 的官方证据核对结果见 [实测记录](tests/fixtures/v02-validation.md)。

完整命令、输入格式、20 条规则、证据复核和调度说明见 [运行指南](f1-knowledge/references/runtime.md)。只复制 `f1-knowledge/` 仍可使用原有可迁移技能；使用计算程序需要整个仓库中的 `f1tracker/`。

## 验证 / Validation

```bash
python3 -m unittest discover -s tests -v
```

Automated tests exercise all 20 metrics, ties, session separation, bounded history, revisions, pagination, failures, recovery, backups and quiet no-op execution using synthetic data. A [small real-data replay](tests/fixtures/README.md) checks the 2024 Bahrain/Saudi Arabian results and grids against Formula1.com facts. [Behavioral scenarios](tests/scenarios.md) also include research/host behavior that still requires manual review. These tests do not establish live API availability or the accuracy of a complete historical database.

MIT licensed. Unofficial project, not affiliated with Formula 1 or FIA. Source data retain their respective rights; the license covers this repository's original code and instructions.
