# Narrow Research Problem Reset

日期：2026-08-29。范围是六个窄机制候选的第一轮低成本筛选。每个候选只执行一个 OpenAlex 查询、最多一页、最多一次重试。本轮结果只用于排序，不构成全文科学核验，也不允许据此宣布 novelty。

## 决策摘要

六个 snapshot 保存在 `D:\huancun\BDCI\bdci-research-agent\.pilot-cache\research-topic-reset-20260829\`，该目录已被 `.gitignore` 排除。本轮共 6 次请求，总耗时约 15,419 ms。

| candidate | query | result | closest-work signal | first-round decision |
|---|---|---|---|---|
| `state_aware_context_handoff` | `multi-agent state handoff context transfer agents` | 24, partial | taxonomy、泛 Agent、mobile-agent 状态迁移 | `evidence_insufficient` |
| `trace_consistent_recovery` | `multi-agent agent recovery execution trace checkpoint failure` | 25, success | checkpoint、fault-tolerance、recovery | `retain_for_full_text` |
| `budget_aware_failure_recovery` | `budget-aware failure recovery long-horizon LLM agents` | 23, partial | AEGIS、faulty-agent collaboration、AgentA/B | `no_go_for_now` |
| `skill_behavioral_regression` | `behavioral regression testing evolving LLM agent skills` | 25, success | LLM survey、领域评估，缺 Skill-specific 机制 | `evidence_insufficient` |
| `interruptible_execution` | `interruptible resumable long-horizon LLM agents checkpoint` | 24, partial | pause/resume、checkpoint、state-aware runtime、AgentRewind | `retain_for_full_text` |
| `artifact_retry_consistency` | `research artifact consistency agent retries provenance` | 24, partial | DREAMS、artifact lineage、provenance | `no_go_for_now` |

最多两个候选进入下一阶段全文核验：`interruptible_execution` 和 `trace_consistent_recovery`。它们的单一运行时机制边界比 artifact consistency 更清楚；后者当前更像 provenance、重试和工程流水线的组合，不能仅凭术语包装保留。

`retain_for_full_text` 只表示值得投入有限全文核验预算，不是 `go`，更不是进入 Method Design 的许可。没有召回可靠近邻时统一使用 `evidence_insufficient`，绝不解释为“非常新”。

## 统一判断边界

工程贡献和论文贡献分开记录。JiuwenSwarm 的 RunContext seam、member Rail 隔离、测试和 usage tracking 是真实的框架工程贡献，但不能直接当作论文算法创新。新增 metadata/source id、reviewer 或 rollback 按钮、串联已有模块、换 Prompt，或把已有指标放在一张表里，单独都不构成论文贡献。

## 六个候选的完整定义

### 1. state-aware context handoff

```yaml
research_object: 多 Agent 长任务中的状态交接包和可执行恢复状态
problem_statement: 自然语言摘要会丢失未完成动作、依赖和恢复点，导致接手 Agent 重复或错误执行
single_mechanism: 由阶段、依赖、未完成动作和恢复点组成的 state-transition handoff contract
hypothesis: 状态约束 handoff 相比摘要 handoff 降低状态丢失和重复动作，同时控制传输 token
closest_prior_work_risk: multi-agent communication、workflow checkpoint、state-aware runtime 可能已覆盖核心机制
baseline_1: 只传 initial_query 或自然语言摘要
baseline_2: 完整共享上一 Agent 上下文或 checkpoint
metrics: handoff state-loss rate、重复动作率、任务成功率、handoff token cost、恢复延迟
dataset_task: 固定多 Agent 科研检索、证据整理、实验规划任务并注入故障点
resource_budget: 离线任务集，每条件 20 至 30 个任务、3 个故障点
```

近邻线索：`AI Agents vs. Agentic AI: A Conceptual taxonomy, applications and challenges`（`W4413427262`，2025）；`Intelligent multi-agent reinforcement learning model for resources allocation in cloud computing`（`W4225709846`，2022）；`Mobile agent security`（`W10242621`，1999）。查询返回 partial、24 条。直接机制证据不足，实验可构造，结论为 `evidence_insufficient`。

### 2. trace-consistent multi-agent recovery

```yaml
research_object: 多 Agent 失败后的 trace、checkpoint 与恢复决策
problem_statement: 从不一致历史继续执行会造成重复工具调用、错误 artifact 和不可解释恢复路径
single_mechanism: 以 trace-consistency invariant 约束恢复点，只允许从与已提交 artifact/依赖一致的 checkpoint 继续
hypothesis: trace-consistent recovery 降低 artifact corruption 和重复动作，同时保持恢复成功率
closest_prior_work_risk: 分布式 checkpoint、fault-tolerant workflow、mobile-agent recovery 可能已覆盖相邻问题
baseline_1: 从最近 checkpoint 直接 resume
baseline_2: 失败后从任务起点重跑
metrics: recovery success rate、artifact inconsistency rate、重复工具调用率、recovery latency、额外 token cost
dataset_task: 固定科研 workflow，注入 tool timeout、member failure、invalid output
resource_budget: 离线 replay，每任务最多 3 次恢复并限制工具调用数
```

近邻线索：`Mobile agent security`（`W10242621`）；`Applying mobile agents to intrusion detection and response`（`W1516905725`）；`Intelligent multi-agent reinforcement learning model for resources allocation in cloud computing`（`W4225709846`）。查询返回 success、25 条。机制具体但 LLM 科研 Agent 直接证据不足，结论为 `retain_for_full_text`。

### 3. budget-aware failure recovery

```yaml
research_object: token、工具调用和时间预算受限时的 Agent 失败恢复
problem_statement: 盲目重试可能恢复任务但耗尽预算，立即终止又会丢失可恢复进展
single_mechanism: 基于剩余预算和失败类型，在 resume/retry/degrade/abort 间选择 recovery action
hypothesis: 预算感知恢复提高固定预算下的完成率并降低无效重试成本
closest_prior_work_risk: 可能只是 fault tolerance 加资源调度或 AgentA/B 类成本控制的流程组合
baseline_1: 固定次数 retry
baseline_2: 不考虑预算的最近 checkpoint resume
metrics: budget-normalized task success、wasted retry rate、token/tool cost、恢复延迟、failure containment rate
dataset_task: 带可控故障的多 Agent 科研 workflow，分别设置 token、调用次数、墙钟预算
resource_budget: 离线 replay，每条件最多 30 个任务
```

近邻线索：`AgentA/B: Automated and Scalable Web A/BTesting with Interactive LLM Agents`（`W4415157977`）；`The Rise of Agentic AI: A Review of Definitions, Frameworks, Architectures, Applications, Evaluation Metrics, and Challenges`（`W4414023998`）；`Challenges and Applications of Large Language Models`（`W4384920109`）。查询返回 partial、23 条。实验可行但直接机制不足，且与候选 2 重叠，结论为 `no_go_for_now`。

### 4. behavioral regression detection for evolving Skills

```yaml
research_object: Agent Skill 更新后的行为回归和能力退化检测
problem_statement: Skill 变化可能改善新任务，却破坏既有任务和安全约束
single_mechanism: 以行为契约为核心，对 Skill 版本更新前后固定轨迹做差分并输出阻断信号
hypothesis: 契约驱动轨迹差分比单一成功率检查更早发现隐性回归
closest_prior_work_risk: 软件回归测试、LLM evaluation、self-evolution safety 可能已覆盖该流程
baseline_1: 只运行新任务成功率测试
baseline_2: 固定回归任务集 pass/fail
metrics: regression detection precision/recall、invalid activation rate、capability gain、regression rate、test cost
dataset_task: 固定科研工具任务和合成 Skill 版本变更，包含成功、回归、误报样本
resource_budget: 离线轨迹 replay，每版本最多两轮测试，不自动部署
```

近邻线索：`A Survey of Large Language Models`（`W4362515116`）；`Large language models (LLMs): survey, technical frameworks, and future challenges`（`W4401671778`）；`Large language models could change the future of behavioral healthcare: a proposal for responsible development and evaluation`（`W4393397034`）。查询返回 success、25 条，但没有直接 Skill regression 机制。不能把未命中解释为新颖，结论为 `evidence_insufficient`。

### 5. interruptible resumable long-horizon Agent execution

```yaml
research_object: 长时 Agent 被中断后基于一致状态安全恢复的运行时机制
problem_statement: 中断发生在工具调用、artifact 写入或 member 边界时，简单 resume 可能重复副作用或丢失进展
single_mechanism: 将 side-effect boundary、恢复 token 和可验证 checkpoint 绑定为原子 resume decision
hypothesis: 该协议相比无条件 resume 或从头重跑，提高有效完成率并减少副作用重复
closest_prior_work_risk: pause/resume、checkpoint runtime、AgentRewind 和 state management 可能覆盖核心空间
baseline_1: 从最近保存状态无条件 resume
baseline_2: 中断后从任务起点重新执行
metrics: resume success rate、duplicate side-effect rate、lost-progress rate、recovery latency、token cost
dataset_task: 可中断多 Agent 科研 replay，覆盖工具调用、artifact commit、member handoff 边界
resource_budget: 每任务最多 3 个中断点和 3 次恢复，优先本地模拟工具
```

近邻线索：`The Online Pause and Resume Problem: Optimal Algorithms and An Application to Carbon-Aware Load Shifting`（`W4389609031`，2023）；`Polaris: A Safety-focused LLM Constellation Architecture for Healthcare`（`W4393063231`，2024）；`AgentRewind`（OpenAlex snapshot 中的 2026 相关记录，需核验记录质量和全文）。查询返回 partial、24 条。六个候选中直接机制相关性最强，但仍需全文核验，结论为 `retain_for_full_text`。

### 6. research artifact consistency under Agent retries

```yaml
research_object: 重试和多成员协作下 research artifact、依赖和 provenance 的一致性
problem_statement: 重试可能覆盖、分叉或引用过时 artifact，使论文证据链与实际执行过程不一致
single_mechanism: 基于 artifact dependency graph 的 retry commit validation，只有依赖和 provenance 检查通过才提交结果
hypothesis: 提交校验降低 retry-induced inconsistency 和断裂引用，同时保持可接受开销
closest_prior_work_risk: provenance management、workflow lineage、checkpoint commit 和科研 Agent orchestration 可能已覆盖该机制
baseline_1: 按最后写入结果覆盖 artifact
baseline_2: 每次重试独立版本但不检查依赖一致性
metrics: artifact consistency rate、broken provenance rate、retry success rate、stale-reference rate、token/latency overhead
dataset_task: DREAMS 类科研 artifact 生成任务离线 replay，包含失败重试、并发写入和过时依赖
resource_budget: 固定 snapshot 和本地 artifact graph，每场景最多 3 次 retry
```

近邻线索：`DREAMS: Density Functional Theory Based Research Engine for Agentic Materials Simulation`（`W4417424660`，2025）；`Metadata and Provenance Management`（`W1480529862`，2009）；`Blockchain technology in supply chain management: an organizational theoretic overview and research agenda`（`W4309890836`，2022）。查询返回 partial、24 条。科研语境较强，但单一机制尚未与 provenance/lineage 系统区分，结论为 `no_go_for_now`。

## 下一阶段、资源与边界

全文核验只进入候选 2 和候选 5。两者都必须证明差异改变了恢复决策，而不是记录日志、增加字段或重命名 checkpoint；同时必须有两个 baseline、两个量化指标、公开或可构造任务和可控资源预算，否则明确 `no_go`。

本轮没有 token 统计，不伪造 `observed + 0`。资源记录为：

```yaml
research_run_id: research-topic-reset-20260829
phase: literature
measurement_status: estimated
tool_calls: 6
input_tokens: null
output_tokens: null
wall_time_ms: 15419
reviewer_calls: 0
artifact_path: .pilot-cache/research-topic-reset-20260829/
```

本轮不进入 Method Design，不生成论文初稿，也不接 Stanford Reviewer。六个候选的保留状态仅表示是否进入下一轮证据审查，最终科学决策仍只能是 `candidate = retain` 或 `candidate = no_go`。
