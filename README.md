# F1 Knowledge Skill 🏁

通用、可迁移的 F1 知识 Skill：历史、车手、车队，以及每场大奖赛后有证据可查的冷门纪录追踪。

A portable, evidence-led Formula 1 skill for history, drivers, constructors and unusual post-race records. Chinese and English supported; race reports default to Chinese with English proper names.

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
