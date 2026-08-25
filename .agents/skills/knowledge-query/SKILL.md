---
name: knowledge-query
description: 检索 cannbot-knowledge 中受治理的 CANN、算子、图、模型与 Runtime 知识。回答技术问题、设计、实现、调试、优化、测试或跨技术适配前使用；从经过校验的持久化索引返回平台受限候选，并支持不可覆盖 receipt、decision state、ready 和 outcome 审计链。
---

# Knowledge Query

先搜索候选卡，再选择性打开正文并沿固定来源核验。结果摘要只用于选卡，不替代技术判断、目标平台实验或 Profiling。

## 前置定位

1. 明确目标实体和当前要回答的一个 decision。
2. 确认 domain、technology、路径 Profile 和目标 platform。只有芯片型号、SocVersion 或 NPU 架构时，先读[平台识别](references/platform-identification.md)；无法安全映射就向用户确认。CANN 版本用于命中后核对正文适用范围，不作为搜索过滤条件。
3. 先用 `discover` 区分实际卡片覆盖与只有 Registry/占位目录的规划范围。

Query 只消费已经准备且未过期的索引。缺失或陈旧时停止，并让知识仓维护者或项目安装器执行索引构建；日常查询不临时扫描全库或静默重建。

## 查询

```bash
python3 <skill-dir>/scripts/knowledge_query.py --knowledge-root <repo> search \
  --query "目标 API 或错误信号" --technology ascendc --platform a2
```

优先使用最窄过滤条件。普通搜索必须传目标 platform；平台识别查询和显式未定位 draft 是受控例外。完整参数、索引维护和输出 schema 见 [CLI](references/cli.md)。精确错误码、API 或日志短语使用 `--match literal`。

## 轻量与审计路径

单 API、错误码或窄概念问答使用轻量路径：一条高信息密度 query，读取少量候选，报告结论、证据、冲突/缺口和必要验证。

复杂实现、故障、性能优化、多 decision 或交接任务按[查询与证据工作流](references/query-workflows.md)执行。每个 decision 单独查询并保存不可覆盖 receipt；冻结 state 后以完全相同的目标平台重放每条查询并生成 ready receipt，工程验证结束后再校验 outcome manifest。

按问题侧面选择内部模式：[算子实现](modes/operator-implementation/MODE.md)、[API 选择](modes/api-selection/MODE.md)、[故障诊断](modes/failure-diagnosis/MODE.md)、[性能优化](modes/performance-optimization/MODE.md)或[技术问答](modes/operator-qa/MODE.md)。这些是 Query 的渐进式参考，不是额外 Skill。

## 消费规则

- 默认只返回 `stable`；研究草稿或历史内容时才改变 status。
- `[agnostic]` 可匹配任一目标平台；`platforms: []` 不满足常规平台过滤；Glossary 按平台中立处理。
- 未定位平台的 draft 只在显式 `--include-unlocated --status draft|all` 时返回，不能与 `--platform` 混用。
- 没有 `verified` 是 unverified；非 human event 是 machine-confirmed；至少一个 `human:` event 是 human-reviewed。信任层级影响排序，不等于正确性证明。
- shared 只在显式 `--include-shared` 时附加到目标 technology；其他 DSL 不因关键词相似自动成为证据。
- Query 当前不按 CANN 版本过滤；读取命中卡的正文和 `cann_versions`（若有）后，由调用方判断版本边界。
- 零命中只表示当前条件下未召回，不证明能力不存在。
- `literal` 优先精确标题，再依次考虑标题片段、摘要和正文；`cannbot:related` 管理区块不参与检索。
- 读取命中的 `local_path`，核对正文、平台、版本、失效边界和完整 sources；需要强证据时继续打开固定来源。

保持只读。除调用方明确指定的新 search/ready/outcome receipt 外，不写索引、知识卡或仓库状态。
