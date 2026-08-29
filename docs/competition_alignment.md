# Competition Alignment

日期：2026-08-29。本文根据官方比赛页面的当前核验结果，记录科研 Agent 的交付目标、评测约束、合规风险和本项目的执行边界。

## 官方任务目标

比赛要求开发基于 JiuwenSwarm 的 Agent，自动完成选题拆解、文献调研、方法设计、论文撰写和结果分析，最终输出英文 ICLR 风格短论文。官方列出的“Agent 上下文工程设计”“Agent 记忆引擎设计”“Agent 自演进”是建议赛题主题，不应解释为唯一允许的论文方向。

官方页面：

- [比赛详情](https://www.xir.cn/competition/1167)
- [数据与评测](https://www.xir.cn/competition/1167/dataware)
- [常见问题](https://www.xir.cn/competition/1167/faq)

## 评测与交付重点

当前核验到的评测关注点包括成熟度、先进性、创新性、实用性、普适性、社会效益和商业价值。论文质量占主要分值，但评测也会复核 Agent 源码、文档、资源报告和框架贡献。

FARS 是官方参考标杆，覆盖：

```text
Ideation -> Planning -> Experiment -> Writing
```

因此本项目的目标是形成完整、可复现、证据可追溯的科研生成流水线，而不是单独展示一个 Rail、上下文字段或运行时修复。英文 PDF、ICLR 模板和与最终 PDF 对应的 Reviewer Access Token 也属于提交闭环的一部分。获奖后的代码开源要求以官方最新通知为准。

官方数据页目前核验到：每队每天最多提交 3 次；初赛截止时间为 2026-10-09 24:00；复赛包含长文生成和跨主题泛化测试。页面出现“2026/09/31”，该日期不存在，应视为录入错误，具体时间以赛事平台最新通知或官方群公告为准。

## 当前研究方向状态

此前的科学止损针对的是具体候选问题，不是主题类别本身：

| 层级 | 当前状态 |
|---|---|
| `memory_engine` 主题 | 仍开放，原候选 `no_go` |
| `context_engineering` 主题 | 仍开放，原候选 `no_go` |
| `self_evolution` 主题 | 仍开放，原候选 `no_go` |
| `state_aware_context_handoff` | `evidence_insufficient` |
| `budget_aware_failure_recovery` | `no_go_for_now` |
| `skill_behavioral_regression` | `evidence_insufficient` |
| `artifact_retry_consistency` | `no_go_for_now` |
| `interruptible_execution` | `no_go` |
| `trace_consistent_recovery` | `no_go` |
| Method Design | 暂不启动 |

六个具体候选被淘汰，是因为现有文献覆盖了其主要机制或当前证据不足；这不表示三个建议主题永久不可选。下一轮候选应优先满足论文可完成性、实验可验证性和完整产出质量，不应只追求“没人做过”的底层机制。

## 外部数据合规闸门

官方作品要求中包含“不经允许使用外部数据”。当前不能自行假设 OpenAlex、arXiv、Semantic Scholar 或其他外部文献源可作为最终提交 Agent 的运行时依赖。以下问题必须向赛事群或官方技术答疑确认：

1. 提交 Agent 运行时是否允许访问 OpenAlex、arXiv 等外部文献源？
2. “不经允许使用外部数据”是否只限制训练数据，还是也限制推理时检索？
3. 是否存在官方提供或预先批准的文献数据集？
4. 开发阶段产生的外部文献调研结果能否作为最终论文相关工作依据？

在明确答复前，OpenAlex Pilot 只能作为开发阶段的内部选题研究记录，不能视为最终提交运行数据，也不能让最终 Agent 必须联网。开发与提交边界如下：

```text
开发阶段：允许的情况下使用 OpenAlex 做研究判断，并保留 snapshot/provenance
提交阶段：默认离线，使用获准的文献 corpus + ReplayLiteratureSource
切换真实源：只有获得明确许可后，才启用可替换的 LiteratureSourceAdapter
```

搜索失败、无许可或来源不完整时，不能把结果标记为 verified，更不能用空结果伪装成论文证据。

## 现有能力与评测映射

| 现有能力 | 能支撑的交付价值 | 边界 |
|---|---|---|
| research-run context seam | 研究运行、阶段和产物的可追踪编排 | 不等于论文创新 |
| Team member Rail isolation | 多成员研究状态隔离和系统稳定性 | 不等于新恢复算法 |
| EvidenceBundle、provenance、source hash | 相关工作和研究判断可审查 | 外部数据许可仍待确认 |
| Research Value Gate | 证据优先的选题筛选，区分 mechanical 与 scientific decision | 不证明实验成功 |
| LiteratureSourceAdapter、Replay source | 真实源与离线 corpus 的可替换边界 | 当前默认不依赖真实网络 |
| ResearchUsageRecord | 记录 phase、token、工具调用、重试、时长和产物 | 尚未覆盖完整端到端运行数据 |
| 四项 JiuwenSwarm framework contribution | openJiuwen 贡献、架构和可复现性材料 | 与最终论文科学贡献分开陈述 |

## 离线运行策略

最终提交版本应支持固定文献 corpus 和 ReplayLiteratureSource，不依赖网络可用性、API key 或未获批准的数据源。每个证据必须来自 corpus/source adapter，Gate 只能引用 EvidenceBundle 中存在的 evidence ID；保留 source URI、source hash、摘要/片段、原始快照路径和 research run 关联。

资源记录仍须区分 `observed`、`estimated` 和 `pending`。未知 token 不得写成 `observed + 0`。真实外部请求即使被允许，也只能在有明确请求次数和耗时、没有 token 统计时记录为 `estimated`。

## 当前执行边界

本阶段不启动新的 OpenAlex 检索，不进入 Method Design，不接 Stanford Reviewer、Publication Gate 或真实评测服务。README 继续暂缓，直到候选问题确定、Method Design 通过且首个端到端实验方案稳定。

下一步顺序为：

```text
确认外部文献数据和运行时联网规则
-> 基于正式约束重新生成窄研究问题
-> 使用离线或获准数据进行 Value Gate
-> 只有科学审评通过才进入 Method Design
```
