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

This is an instruction skill, not an autonomous scraper or a preconfigured background service. A host scheduler must invoke it for recurring checks and support quiet no-op delivery. No automation is created by installation. A suitable recurring task prompt is:

> Run f1-knowledge in tracking mode. Check completed GPs since stored state, process backlog chronologically and review provisional claims. Persist reports and provenance. Suppress routine notification if no new GP; emit material corrections or operational errors only as specified by the skill.

详细规则见 [Skill](f1-knowledge/SKILL.md)、[统计定义](f1-knowledge/references/definitions.md)、[状态协议](f1-knowledge/references/state.md)。官方入口：[FIA](https://www.fia.com/documents)、[Formula1.com](https://www.formula1.com/en/results)；历史交叉核验：[STATS F1](https://www.statsf1.com/en/statistiques.aspx)。具体报告必须引用具体文件，入口链接本身不证明纪录。

## 验证 / Validation

Review scenarios in [tests/scenarios.md](tests/scenarios.md). They cover silent no-op, catch-up, revisions, session separation, historical gaps and recovery. This repository defines an agent workflow; live record accuracy depends on the executing host's source access and verification.

MIT licensed. Unofficial project, not affiliated with Formula 1 or FIA. Source data retain their respective rights; the license covers this repository's original code and instructions.
