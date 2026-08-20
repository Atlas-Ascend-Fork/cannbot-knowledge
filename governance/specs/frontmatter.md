# Frontmatter 与证据

Frontmatter 保存检索、适用范围、生命周期和来源等结构化信息。字段类型由 `frontmatter.schema.json` 定义，字段组合和路径 Profile 到 OKF `type` 的映射由 `profiles.yaml` 定义，平台、标签等受控值来自 `registries.yaml`；跨字段和跨文件关系由统一 Contract 检查。机器文件的职责见 [Schema 与 Contract](schemas.md)。

## 公共必选字段

每张非 `index.md` 知识卡必须填写八个公共字段。

| 字段 | 用途 | 约束 |
|---|---|---|
| `type` | OKF 交换类型 | 非空，且等于路径 Profile 的 `okf_type` |
| `title` | 人读标题和主要召回文本 | 非空 |
| `description` | 不打开正文也能理解的摘要 | 非空 |
| `tags` | 工程任务和讨论主题 | 2–6 个、不可重复，至少一个 `task.*` 和一个 `topic.*` |
| `status` | 生命周期和默认查询可见性 | `draft`、`stable` 或 `deprecated` |
| `sources` | 可回到原文或证据的入口 | 数组；非 `draft` 至少一项 |
| `created_at` | 卡片首次形成时间 | UTC RFC 3339 秒精度，以 `Z` 结尾 |
| `updated_at` | 最近一次实质变更时间 | 同上，且不得早于 `created_at` |

最小草稿示例：

```yaml
---
type: Concept
title: 示例概念
description: 说明一个仍待补充证据和范围评审的概念。
tags: [task.lookup, topic.architecture]
status: draft
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-15T00:00:00Z"
platforms: []
---
```

## Profile 字段组合

路径选择 Profile，Profile 再确定唯一 OKF `type`。贡献者不能自由创造另一套映射。

| 路径 Profile | OKF `type` | 额外必选字段 | 可选字段 |
|---|---|---|---|
| `concepts` | `Concept` | `platforms` | `cann_versions`, `aliases`, `verified`, `replaced_by` |
| `apis` | `API` | `platforms` | `cann_versions`, `aliases`, `verified`, `replaced_by` |
| `examples` | `Example` | `platforms` | `cann_versions`, `verified`, `replaced_by` |
| `operators` | `Operator` | `platforms` | `cann_versions`, `verified`, `replaced_by` |
| `optimizations` | `Optimization` | `platforms` | `cann_versions`, `verified`, `replaced_by` |
| `runbooks` | `Runbook` | `platforms` | `cann_versions`, `aliases`, `verified`, `replaced_by` |
| `interoperability` | `Interoperability` | `platforms`, `source_technology`, `target_technology` | `cann_versions`, `verified`, `replaced_by` |
| `glossaries` | `Glossary` | 无 | `aliases`, `verified`, `replaced_by` |

新增字段必须先有稳定语义和实际消费者，再同时修改 Schema、Profile、Contract、文档和回归；不能为单张卡增加临时字段。

## 生命周期与信任

| `status` | 含义 | 默认 Query |
|---|---|---|
| `draft` | 尚未评审、来源不足或适用范围未确认 | 不返回 |
| `stable` | 可以在卡片声明的范围内消费 | 返回 |
| `deprecated` | 为历史引用保留，不再代表当前推荐结论 | 不返回 |

本仓要求显式填写 `status`。已确认错误但仍需解释历史行为的卡片也使用 `deprecated`，并在正文和当天日志说明原因。

`replaced_by` 只用于 `deprecated`，填写 Bundle 内、不带 `.md` 的 Concept ID，例如 `ops/ascendc/apis/new_api`。它不能以 `/` 或 `knowledge/` 开头，不能指向自身，目标卡必须存在。

`verified` 使用 OKF verification event，记录真实 actor 和时间：

```yaml
verified:
  - by: human:reviewer_id
    at: "2026-08-15T08:00:00Z"
```

只有一个事件时可以直接写成 mapping；有多个事件时使用数组。Ingest 创建单个事件，Query 会把两种形态统一解释为事件列表。

Actor 使用 `human:<id>`、`process:<id>` 或 `<producer>/<version>`。没有事件是 `unverified`；只有非 `human:` actor 是 `machine-confirmed`；至少一个 `human:` actor 是 `human-reviewed`。

`status` 和 trust tier 相互独立。固定来源、Lint 通过或旧验证枚举都不能转换成虚假的 `verified` 事件。

## 来源（`sources`）

`sources` 回答“正文结论可以回到哪里核验”。每项使用 OKF `resource`，并可用本仓扩展 `role` 说明证据用途。

```yaml
sources:
  - resource: https://example.com/versioned/document
    role: primary
```

机器约束：

- `stable` 和 `deprecated` 至少有一项来源，只有 `draft` 可以使用 `sources: []`；
- `resource` 当前只接受 HTTP(S)；
- GitCode、GitHub、Gitee 和 GitLab 上的仓库来源必须使用 `blob`、`tree` 或 `raw` 路径，并固定到 40 位 commit；已知 raw 域名同样必须固定到 commit，分支名和裸仓库首页不通过；
- Lint 只检查形状和固定格式，不联网，也不判断来源是否支持结论。

| `role` | 用途 |
|---|---|
| `primary` | 直接定义或说明核心结论 |
| `supporting` | 补充背景、边界或旁证 |
| `example` | 可运行样例或使用方式 |
| `constraint` | 平台、参数、行为或版本限制 |
| `header` | API 声明、类型或编译期接口 |
| `implementation` | 固定版本实现源码 |
| `evidence` | 实验记录、日志、测试或可复现观察 |

`role` 只描述用途，不代表证据质量。贡献者仍需确认来源真实存在、支持正文结论、覆盖所声明的平台和版本，并且没有把搜索摘要、聊天记录或模型记忆作为唯一技术依据。来源暂时无法匿名访问时，应在评审中说明复核方式；完全无法复核的结论保持 `draft`。

## 标签（`tags`）

`tags` 只表达“支持什么工程任务”和“讨论什么主题”，不重复 domain、技术、Profile、平台、版本、来源或生命周期。

| 维度 | 要求 | 示例含义 |
|---|---|---|
| `task.*` | 至少一个 | 设计、实现、调试、优化、测试、迁移、事实查询 |
| `topic.*` | 至少一个 | Tiling、数据搬运、内存、精度、编译、架构 |
| `paradigm.*` | 可选 | 卡片明确讨论的计算范式 |

每张卡选择 2–6 个来自 Registry 的最小充分标签集合，例如：

```yaml
tags: [task.implementation, topic.data_movement, topic.alignment]
```

不要为了增加召回堆叠弱相关标签，也不要临时创造近义标签。稳定名称别名优先放入 Profile 允许的 `aliases`；普通近义表达可以进入标题、摘要或正文。新增或重命名标签时，必须有真实卡消费它，并同步知识卡、Query/Lint 回归和文档。

## 适用范围扩展

- 除 `glossaries` 外都要求 `platforms`。平台无关写 `[agnostic]`，且不能与具体平台混用。
- `platforms: []` 只允许 `draft`，表示范围尚未确认；不使用会随 Registry 变化而改变含义的 `[all]`。
- `cann_versions` 只在证据支持明确版本边界时填写；缺失表示未声明，不表示兼容所有版本。
- `source_technology` 和 `target_technology` 只用于 `Interoperability`，必须引用两个不同的已注册 technology。
- `aliases` 只保存稳定检索名称，仅用于 Profile 明确允许的类型。
- `created_at` 创建后保持不变；正文实质变化时更新 `updated_at`，纯格式调整不更新。

Query 使用标题、摘要、`tags` 和 `aliases` 做词法召回，并用路径 Profile、适用范围和生命周期过滤；Lint 检查字段形状、Profile、注册值、时间、actor 和跨文件引用。结构通过不代表技术结论正确，消费前仍需阅读正文和来源。
