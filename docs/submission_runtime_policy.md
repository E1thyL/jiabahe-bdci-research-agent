# Submission Runtime Policy

科研 Agent 采用联网优先、离线可降级的受控策略：

```text
online permitted and available -> allowlisted source -> cache/provenance -> EvidenceBundle
network unavailable or not permitted -> offline corpus -> EvidenceBundle
both unavailable -> insufficient/revise; never fabricate citations
```

## Literature modes

`LITERATURE_MODE` 支持：

- `offline`：只调用离线 `ReplayLiteratureSource`，不会发 HTTP 请求。
- `online_allowlist`：只调用注入的 OpenAlex 或 arXiv 官方适配器；未配置在线适配器或请求失败时返回 `failed`，不自动绕过策略。
- `auto`：优先在线；在线异常或返回 `failed` 时切换离线 corpus。

在线适配器必须声明 allowlisted source 和官方 endpoint。路由器拒绝未知来源和非官方 host，不提供任意网页浏览能力。当前仓库不实现真实 DeepSeek 传输；`OfficialDeepSeekClient` 只是官方 DeepSeek V4 Flash 的注入协议，调用方负责提供官方 endpoint 和真实用量。

## Evidence and provenance

在线结果必须继续经过现有 adapter 的 provenance 校验，使用 `source_uri`、稳定 `source_hash`、`evidence_id` 和与 `research_run_id` 关联的 artifact/cache。HTTP 成功不等于论文结论科学验证；搜索失败或空结果不能生成 verified evidence，也不能伪造引用。

## Usage semantics

没有 token/tool 统计时，usage record 使用 `measurement_status=pending`，未知 token 保持 `null`。只有明确请求次数或耗时等估算依据时使用 `estimated`；有 provider 返回的完整观测值才使用 `observed`。离线确定性 replay 可以记录零工具调用，但必须明确它不是一次真实网络搜索。

## Submission boundary

开发阶段可以在规则允许时使用 OpenAlex/arXiv 发现最新工作并缓存快照。正式提交不得把公网作为唯一生存条件，默认必须能用获准的本地 corpus 完成运行。是否允许提交时访问外部文献源、是否允许携带 metadata snapshot，仍以赛事官方书面答复为准。
