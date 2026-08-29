# Execution Recovery Gap Decision

日期：2026-08-29。本文对 `interruptible_execution` 和 `trace_consistent_recovery` 做最后一轮全文价值审评。全文核验使用公开 arXiv PDF；OpenAlex 的来源记录用于发现工作，不把 OpenAlex 的 `verified` 解释为科学结论已验证。

## 结论

```yaml
interruptible_execution: no_go
trace_consistent_recovery: no_go
method_design: prohibited
```

核心原因不是两个问题不重要，而是最接近的全文工作已经覆盖了候选机制的关键部分：AgentRewind 覆盖对齐的 Agent context/environment checkpoint、checkpoint 选择、rewind memory 和恢复评测；DART 覆盖失败实例定位、语义可恢复边界、依赖/副作用约束和 admissible restore point。把这些机制换成“科研 Agent”“trace consistency”或“artifact consistency”目前仍是应用场景和术语变化，不足以形成独立算法贡献。

## 检索范围

本轮使用四个受控查询，每个查询一页，最多一次重试：

1. `interruptible long-horizon LLM agent execution`
2. `agent checkpoint resume recovery state`
3. `trace consistent recovery autonomous agent`
4. `execution trace based recovery LLM agent`

查询结果有噪声，且部分 2026 记录较新。最终只将能取得公开全文并且能直接核验机制的三篇工作纳入比较。未把无法全文核验的条目或摘要-only 记录当作独立科学证据。

## 全文核验记录

### AgentRewind: Recoverable Execution for Long-Horizon LLM Agents

| 字段 | 核验值 |
|---|---|
| authors | Yu Zhuang, Kefei Chen, Yitong Duan, Shuxin Zheng, Jian Li, Xu-Yao Zhang |
| year / venue | 2026 / arXiv preprint `arXiv:2608.14380v1` |
| source_uri | https://arxiv.org/abs/2608.14380 |
| full_text_uri | https://arxiv.org/pdf/2608.14380 |
| evidence_id | `arxiv-2608.14380-fulltext` |
| source_hash | `23557f4860268d22cf0fcbd8faae25a5d20f54b5ea208fc2bd11653ab2168b33` |
| section / page | Abstract, Introduction, AgentRewind Framework, External Environment Recovery Boundary, pp. 1, 3-5 |
| original excerpt | “records aligned checkpoints of the agent context and controlled environment”; “select an earlier checkpoint”; “restores both the agent context and the environment state”; effects outside the workspace filesystem “cannot be undone.” |
| scientific_verification | `verified` for the quoted mechanism and stated evaluation; benchmark claims are reported claims, not independently reproduced |

全文显示：checkpoint 是 Agent context 与 environment state 的对齐状态；Agent 在当前轨迹不能继续时选择历史 checkpoint；系统注入 rewind memory 后生成新的 suffix；workspace 文件状态可恢复，但网络请求和外部服务状态不能撤销；MettleBench 使用 task success 和 checklist prefix progress 评估。因此候选一提出的中断恢复、状态恢复、副作用边界和恢复正确性均有直接强先例。

### DART: Semantic Recoverability for Structured Tool Agents

| 字段 | 核验值 |
|---|---|
| authors | Ke Yang, Panpan Li, Zonghan Wu, Kejin Xu, Huaxi Huang, Xiaoshui Huang |
| year / venue | 2026 / arXiv preprint `arXiv:2605.23311v1` |
| source_uri | https://arxiv.org/abs/2605.23311 |
| full_text_uri | https://arxiv.org/pdf/2605.23311 |
| evidence_id | `arxiv-2605.23311-fulltext` |
| source_hash | `8e57b882c47c9456edc88e4c012041d07e171415fb769ffb7e10f546b5a1e572` |
| section / page | Abstract, Introduction, Related Work, Problem Setting, pp. 1-4 |
| original excerpt | “controller legality ... does not imply semantic validity”; DART performs “failed-instance localization, recoverable-boundary certification, instance-aligned checkpointing, and admissible rollback selection”; failed conditions block local rollback and fall back to whole-task rerun. |
| scientific_verification | `verified` for the formalized mechanism and decision procedure; experiments are not independently reproduced |

全文显示：DART 让 trace、实例边界、依赖关系和 effect constraints 进入恢复准入决策；定义 decidability、closure、separability、controllability 四类边界条件，并在不满足条件时阻断局部恢复。它直接覆盖候选二所谓“定位失败阶段并选择不会破坏成果的恢复动作”。

### Reflexion: Language Agents with Verbal Reinforcement Learning

| 字段 | 核验值 |
|---|---|
| authors | Noah Shinn, Federico Cassano, Edward Berman, Ashwin Gopinath, Karthik Narasimhan, Shunyu Yao |
| year / venue | 2023 / arXiv preprint `arXiv:2303.11366v4` |
| source_uri | https://openalex.org/works/W4353112996 |
| full_text_uri | https://arxiv.org/pdf/2303.11366 |
| evidence_id | `arxiv-2303.11366-fulltext` |
| source_hash | `6059b6f89fea9959bd3dab553fbb97756a3dfb1b15e3cbab2fbf3ab6664333bd` |
| section / page | Abstract, Introduction, Reflexion: reinforcement via verbal reflection, pp. 1, 3-4 |
| original excerpt | “verbally reflect on task feedback signals, then maintain their own reflective text in an episodic memory buffer”; prior trajectories become verbal reinforcement cues for the next attempt. |
| scientific_verification | `verified` for trace/feedback use in later decisions; it is an adjacent prior, not evidence of checkpoint restoration |

Reflexion 不提供物理 checkpoint 或 environment rollback，但证明 execution history/feedback 可以进入后续行动选择和 episodic memory。因此“trace 参与下一次决策”本身不能声称为新机制。

## Candidate A：interruptible_execution

工作问题：长时 Agent 被中断后，如何根据语义状态选择恢复点并保证恢复行为与任务目标一致？

### overlap matrix

| 维度 | AgentRewind | DART | Reflexion | Candidate A |
|---|---|---|---|---|
| interruption model | 轨迹错误/无法继续时 rewind | 结构化 Agent 失败实例 | 试次失败后下一 episode | 中断、工具边界或 member 边界 |
| state representation | context + controlled environment | FSM state、action、memory delta、history | trajectory + reflective text | 语义状态、恢复 token、checkpoint |
| checkpoint selection | Agent 从历史 metadata 选择 | admissible restore point | 无物理 checkpoint | 根据语义状态选择 |
| resume policy | restore、注入 rewind memory、生成新 suffix | admissible rollback 或 whole-task rerun | 反馈后下一次尝试 | 一致性约束下 resume |
| trace usage | checkpoint metadata 和 trajectory | failed-instance localization、history | feedback/trajectory 影响后续 policy | trace 约束恢复 |
| artifact consistency | workspace 状态回滚 | downstream commitment 的依赖/effect constraints | 未处理 artifact rollback | artifact/依赖一致性 |
| side-effect handling | workspace 可回滚，外部 effect 不可撤销 | effect boundary，阻断不安全 rollback | 未处理物理副作用 | side-effect boundary |
| failure localization | 轨迹触发 rewind | 明确定位 failed instance | evaluator 反馈，不是 runtime localization | 判断失败阶段 |
| recovery action selection | 选择 rewind checkpoint | rollback 或 block/rerun | 改进下一 episode | resume/retry/abort |
| correctness metric | task success、checklist progress | correct/unsafe recovery | task success、pass@1 | recovery correctness |
| cost / latency | 多模型运行时评测 | local recovery 与 rerun 对比 | 额外 reflection episodes | token、latency |

### 判断

候选 A 的“side-effect boundary + recovery token + verifiable checkpoint 的原子 resume decision”没有显示出区别于 AgentRewind 对齐 checkpoint、DART admissibility guard 的新算法。AgentRewind 已处理上下文和环境联合恢复、checkpoint 选择和外部副作用边界；DART 已处理语义有效性而非仅机械可恢复性。候选 A 最多是迁移到科研 Agent 的应用化工程问题，判定 `no_go`。

无条件 resume、从头重跑等 baseline 以及 success、divergence、duplicate side-effect、latency、token 等指标都可以设计，但指标不能补足缺失的独立机制。

## Candidate B：trace_consistent_recovery

工作问题：如何利用 execution trace 和 research artifact 状态定位失败阶段，并选择不会破坏已有成果的恢复动作？

### overlap matrix

| 维度 | AgentRewind | DART | Reflexion | Candidate B |
|---|---|---|---|---|
| failure model | 轨迹错误导致无法继续 | failed instance 与 commitment-sensitive failure | 环境反馈或测试失败 | 阶段性 Agent failure |
| trace usage | 恢复轨迹和 checkpoint metadata | history、依赖和 effect constraints 进入准入判断 | trajectory 转 reflection 影响下一次行为 | trace 参与定位和决策 |
| artifact consistency | workspace checkpoint restore | downstream committed work 必须语义有效 | 不处理 artifact consistency | artifact graph + trace invariant |
| recovery policy | 选择 rewind checkpoint | 四步 procedure 选择 admissible rollback 或 block | 下一 episode 改进行为 | resume/retry/degrade/abort |
| failure localization | 轨迹触发 rewind | 明确 failed-instance localization | evaluator/heuristic 归因 | trace-based localization |
| side-effect handling | 外部 effect 不可撤销但不重复 prefix | effect constraints 和 irreversible boundary | 无物理 side-effect policy | 避免副作用重复 |
| correctness invariant | 对齐 context/environment checkpoint | semantic recoverability、closure、separability、controllability | 无形式恢复不变量 | trace/artifact consistency |
| metrics | success、partial progress | recovery correctness、unsafe rollback、replay cost | task success、pass@1 | consistency、duplicate action、recovery success |
| baseline | forward-only / other strategies | entry-only restore、whole-task rerun | base agent / feedback variants | latest checkpoint、restart |
| cost | runtime recording and rewind | consistency checks plus rerun | extra reflection episodes | trace checking overhead |

### 判断

候选 B 比候选 A 更容易写出可计算不变量，但 DART 已经把 trace/history、失败实例定位、下游 commitment、依赖和 effect constraint 组合成恢复选择机制，并在条件不满足时阻断局部恢复。候选 B 若只是把 DART 的语义恢复边界改称“trace consistency”，就是直接重命名；若只增加 artifact metadata，则不是算法贡献。Reflexion 还表明 trace/feedback 驱动后续决策已有先例。因此当前没有被全文证据支持的非重命名技术 gap，判定 `no_go`。

可以构造 baseline 和 consistency 指标，但无法合理宣称候选算法独立于 DART 的 admissibility procedure。

## 科研 Agent 特殊价值与资源判断

科研任务确实有 artifact、证据链和多成员协作的特殊风险，但“把通用恢复机制用于科研 artifact”只证明应用价值，不自动形成论文创新。若未来重新定义问题，必须提出新的恢复选择算法或可证明不变量，并展示它解决了 AgentRewind/DART 未解决的具体失败模式。

本轮全文下载和人工核验没有模型调用，不生成虚假 token 记录。检索阶段资源语义为：

```yaml
research_run_id: execution-recovery-gap-20260829
phase: literature
measurement_status: estimated
tool_calls: 4
input_tokens: null
output_tokens: null
reviewer_calls: 0
artifact_path: .pilot-cache/execution-recovery-gap-20260829/
```

## 最终边界

两个候选均不得进入 Method Design。JiuwenSwarm 的 interrupt/resume、RunContext、Rail 隔离、trace 和 usage 记录仍可作为系统工程贡献或实验基础设施，但不能在没有新算法的情况下写成论文科学贡献。下一步应启动新的窄问题战略评审，而不是继续包装 checkpoint、trace、replay 或 artifact metadata。
