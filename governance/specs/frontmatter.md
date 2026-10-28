# Frontmatter 与证据

Frontmatter 保存检索、适用范围、生命周期和来源等结构化信息。字段类型由 `frontmatter.schema.json` 定义，字段组合和路径 Profile 到 OKF `type` 的映射由 `profiles.yaml` 定义，平台、标签等受控值来自 `registries.yaml`；跨字段和跨文件关系由统一 Contract 检查。机器文件的职责见 [Schema 与 Contract](schemas.md)。

## 公共必选字段

每张非 `index.md` 知识卡必须填写八个公共字段。

公共与 Profile 附加必选字段以 `profiles.yaml` 为唯一机器事实源：缺少字段报告 `frontmatter.required`；已填写但 `title` 或 `description` 为空白文本时报告 `frontmatter.text`。Schema 负责字段类型与形状，不重复顶层必选或这两个字段的非空语义。

| 字段 | 用途 | 约束 |
|---|---|---|
| `type` | OKF 交换类型 | 非空，且等于路径 Profile 的 `okf_type` |
| `title` | 人读标题和主要召回文本 | 非空 |
| `description` | 不打开正文也能理解的摘要 | 非空 |
| `tags` | 工程任务和讨论主题 | 2–6 个、不可重复，至少一个 `task.*` 和一个 `topic.*` |
| `status` | 生命周期和默认查询可见性 | `draft`、`stable` 或 `deprecated` |
| `sources` | 可回到原文或证据的入口 | 数组；轨迹型 `Runbook` 可为空，其他非 `draft` 卡至少一项 |
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
| `concepts` | `Concept` | `platforms` | `cann_versions`, `aliases`, `verified`, `replaced_by`, `scope` |
| `apis` | `API` | `platforms` | `cann_versions`, `source_headers`, `aliases`, `verified`, `replaced_by` |
| `examples` | `Example` | `platforms` | `cann_versions`, `verified`, `replaced_by` |
| `guides` | `Guide` | `platforms` | `cann_versions`, `aliases`, `verified`, `replaced_by`, `scope` |
| `operators` | `Operator` | `platforms` | `cann_versions`, `verified`, `replaced_by` |
| `optimizations` | `Optimization` | `platforms` | `cann_versions`, `verified`, `replaced_by`, `scope` |
| `runbooks` | `Runbook` | `platforms` | `aliases`, `verified`, `replaced_by`, `scope` |
| `interoperability` | `Interoperability` | `platforms`, `source_technology`, `target_technology` | `cann_versions`, `verified`, `replaced_by` |
| `glossaries` | `Glossary` | 无 | `aliases`, `verified`, `replaced_by` |

新增字段必须先有稳定语义和实际消费者，再同时修改 Schema、Profile、Contract、文档和回归；不能为单张卡增加临时字段。

## 场景适用条件（`scope`）

`scope` 是可选的适用条件声明，不代替路径、平台、标签、来源或复核事件。字段结构由 Schema 定义，维度类型、值和别名由 Registry 的 `scope_schemas` 定义，统一 Scope Contract 执行维度校验与三态匹配。当前仅注册 `model.inference.v1`，绑定 `model/inference` 路由；字段只用于 Profile 允许的卡片，不为其他领域预注册占位 namespace。

维护时遵守三条原则：

1. **可选**：不是每张卡都需要 Scope；没有明确限制或没有过滤价值时可以省略，不以填写率作为卡片质量或迁移完成标准。
2. **允许部分声明**：来源支持且能帮助过滤的条件即可提取，不要求全部维度已知。例如只声明 `phase: [prefill]`，Contract 与已确认的 Decode 条件比较时仍能识别冲突；查询额外指定了卡片未声明的执行模式时，比较结果保留为未知。不得为凑齐字段补写 `any`、否定条件或未核实的范围。
3. **按领域扩展**：各领域独立定义 namespace、适用范围、维度和匹配语义。公共部分只共享对象外壳、场景 AND/OR 组合与三态结果协议；不要求其他领域使用 Prefill、Decode、MoE 等模型推理字段。已有匹配类型不足时，在受审查的 Contract 处理器中扩展，再由 Registry 选择，不在知识卡中保存可执行判断。注册与权限边界见 [机器契约](schemas.md)。

以下维度、词表和否定权限属于当前模型推理 Schema；其他领域按各自注册定义使用。

```yaml
scope:
  schema: model.inference.v1
  any_of:
    - all_of:
        phase: [prefill]
        execution_mode: [ge_graph]
        objective: [ttft]
        context_length: [long_context]
        batch_size: [small_batch]
    - all_of:
        phase: [decode]
        execution_mode: [eager]
        model_features:
          all_of: [moe, mla]
```

多个场景分支之间是 OR；分支内不同维度是 AND；普通枚举数组内是 OR；`required_set` 的 `all_of` 表示必需集合。`model_features`、`parallelism`、`deployment_topology` 是集合维度。序列长度、batch、并发、服务形态和部署拓扑分别声明，定性值不隐含数值阈值。`objective` 在 Contract 中按精确值匹配；`latency` 不隐含 `ttft` 或 `tpot`，来源支持多个目标时在卡片显式列出，例如 `objective: [latency, tpot]`。

卡片缺少维度表示未声明，查询缺少卡片所需条件表示前提未确认，两者均不能推导普遍适用。枚举维度的 `[any]` 独占使用，表示来源足以支持结论不受该维度限制；集合维度不接受 `any`。集合否定条件由 Registry 分别声明卡片和查询的准入：`model_features.none_of` 仍仅用于显式已确认的查询，卡片只声明必需模型特征；`parallelism.none_of` 可用于来源支持的卡片和显式已确认的查询，表示列出的并行方式没有启用。未提及某个特征或并行方式仍是未知。

```yaml
scope:
  schema: model.inference.v1
  any_of:
    - all_of:
        phase: [prefill]
        parallelism:
          none_of: [cp]
```

上例要求 Prefill 且未启用 CP，不代表单卡，也不排除 TP、EP 等其他并行。集合内可同时写 `all_of` 与 `none_of`，分别表示必须启用与必须未启用，两者为 AND；`none_of` 列出的每一项都须确认未启用。至少出现一项非空列表，且不能要求和排除同一个值。不能根据来源没有提及某种并行就为卡片补否定条件。

| 查询已确认条件 | 卡片要求 `parallelism.none_of: [cp]` 时 |
| --- | --- |
| `parallelism.all_of: [cp]` | `conflict`，明确冲突 |
| `parallelism.none_of: [cp]` | 满足这一项限制；其他维度继续核对 |
| 只声明 `parallelism.all_of: [tp]` | `unknown`，TP 不证明 CP 已关闭 |
| 没有声明 `parallelism` | `unknown`，CP 状态待确认 |

Scope Contract 的比较结果为 `match`、`unknown` 或 `conflict`。缺少卡片 Scope、缺少必要条件或不同的已注册 namespace 均保留未知，非法 Scope 报错。匹配表示声明条件相容，不替代正文、来源与版本核对，也不证明性能已经验证。

当前基础治理在加载卡片、Lint 和构图时校验该字段，并提供统一的三态比较接口。Query 的现有公开接口不接受场景 Scope 过滤参数；卡片声明 Scope 不代表检索已启用该过滤。检索参数及结果结构以 Query Skill 的实际能力为准，无 Scope 的原查询流程保持不变。

## 生命周期与信任

| `status` | 含义 | 默认 Query |
|---|---|---|
| `draft` | 尚未评审、来源不足或适用范围未确认 | 不返回 |
| `stable` | 可以在卡片声明的范围内消费 | 返回 |
| `deprecated` | 为历史引用保留，不再代表当前推荐结论 | 不返回 |

本仓要求显式填写 `status`。已确认错误但仍需解释历史行为的卡片也使用 `deprecated`，并在正文和当天日志说明原因。

`replaced_by` 只用于 `deprecated`，填写 Bundle 内、不带 `.md` 的规范 Concept ID，例如 `ops/ascendc/apis/new_api`。它不能以 `/` 或 `knowledge/` 开头，也不能用 `.` 或重复分隔符构造路径别名；目标必须是符合路径 Profile 的现有知识卡，不能指向自身、`index.md` 或经符号链接越出 Bundle。

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

仓库也可以引用通过登记的获取流程恢复、但不提交到 Git 的本地官方资料：

```yaml
sources:
  - resource: cann-docs-raw/asc-devkit/docs/zh/api/AI-CPU-API/assert.md
    role: primary
```

机器约束：

- 轨迹沉淀的 `Runbook` 可以使用 `sources: []`：正文中的触发、探针、原始观测和验证信号就是可消费证据，不把中间整理仓或会话轨迹伪装成权威 resource；
- 除 `Runbook` 外，`stable` 和 `deprecated` 至少有一项来源，`draft` 可以使用 `sources: []`；
- `resource` 接受 HTTP(S) URL 或已登记的本地来源；本地路径必须位于 Registry 登记的来源根目录中，不得是绝对路径、包含 `..`、反斜杠、查询参数或 fragment；Git 来源根可使用安全的多级相对路径，不能位于知识或治理设施目录中，也不能与其他来源根重叠；
- GitCode、GitHub、Gitee、GitLab、Bitbucket 和 Codeberg 上的文件、目录和 raw 来源必须固定到 40 位 commit，分支名和裸仓库首页不通过；GitCode/GitHub PR 与 Issue 可以直接使用对应仓库的规范工作项 URL，不要求 commit；
- Git 本地来源使用 `cann-ops-raw/ascendc/ops-nn/<40位commit>/<文件路径>` 等 Registry 登记路径，相对于知识仓根；四个算子仓统一放在 `cann-ops-raw/ascendc/<仓库名>/` 下，Runtime 仓放在 `cann-runtime-raw/runtime/` 下。Registry 的 `repository` 与 `revisions` 保留远程来源和版本身份，统一获取入口按固定提交恢复，不跟随分支；
- 正文源码链接相对于卡片目录，可带 `#L71` 或 `#L71-L80` 行号，仅作来源导航，不生成 Concept，也不允许索引跳出 Bundle。已恢复 checkout 必须来源、提交和工作区一致；不能覆盖有本地修改的源码，也不能为原提交中不存在的路径伪造或替换版本，此时应保留固定远程来源并报告缺口；
- 本地来源必须由仓库记录的获取流程提供；全库 Lint 要求获取脚本存在且可执行。当前 `cann-docs-raw/` 由 `get_resources.sh` 按 Registry 的 `archive_url` 恢复，并保持 Git 忽略；官方文档持续更新，不校验归档或内容树 SHA-256。本地根存在时，Lint 检查 `.complete` 的来源 URL 和被引用文件；
- Lint 不联网，也不判断来源是否支持结论；本地根尚未恢复时只检查注册路径形状。

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
| `topic.*` | 至少一个 | Tiling、数据搬运、内存、精度、编译、架构；可使用 Registry 中更精确的多段层级 ID |
| `paradigm.*` | 可选 | 卡片明确讨论的计算范式 |

每张卡选择 2–6 个来自 Registry 的最小充分标签集合，例如：

```yaml
tags: [task.implementation, topic.data_movement, topic.alignment]
```

不要为了增加召回堆叠弱相关标签，也不要临时创造近义标签。稳定名称别名优先放入 Profile 允许的 `aliases`；普通近义表达可以进入标题、摘要或正文。新增或重命名标签时，必须有真实卡消费它，并同步知识卡、Query/Lint 回归和文档。

## 适用范围扩展

- 除 `glossaries` 外都要求 `platforms`。平台无关写 `[agnostic]`，且不能与具体平台混用。
- `platforms: []` 只允许 `draft`，表示范围尚未确认；不使用会随 Registry 变化而改变含义的 `[all]`。
- `cann_versions` 只在证据支持明确版本边界时填写；缺失表示未声明，不表示兼容所有版本。Runbook 不使用该字段（版本边界若确属结论一部分，写入正文失效边界）。
- `source_technology` 和 `target_technology` 只用于 `Interoperability`，必须引用两个不同的已注册 technology。
- `aliases` 只保存稳定检索名称，仅用于 Profile 明确允许的类型。
- `created_at` 创建后保持不变；正文实质变化时更新 `updated_at`，纯格式调整不更新。

Query 使用标题、摘要、`tags`、`aliases` 和正文做词法召回，并用路径 Profile、适用范围和生命周期过滤；Lint 检查字段形状、Profile、注册值、时间、actor 和跨文件引用。结构通过不代表技术结论正确，消费前仍需阅读正文和来源。

## 源码头文件（`source_headers`）

`source_headers` 只用于 `apis` 卡片，给出该 API 的源码头文件相对路径，作为 agent 在本机 CANN 源码/安装包中定位其声明与内联实现源码的线索。路径相对该 API 对应的源码/组件根：Ascend C 使用 asc-devkit 根，Runtime 使用其固定 Runtime 源码根。源码树布局不必等于安装包布局；安装包应按实际 include 配置确认归属，不跨技术拼接。例如 Ascend C 公开头文件位于组件根的 `include/` 下：

```yaml
source_headers:
- include/basic_api/kernel_operator_set_atomic_intf.h
- include/c_api/asc_simd.h
```

约束：

- 去重数组，元素必须是非空字符串；没有头文件定位证据时省略该字段，空数组不代表 API 没有声明头文件。该字段不代替 `sources` 的固定版本证据。
- 读取时先确认对应源码或组件根，再拼接为绝对路径，不能相对于知识卡或当前工作目录打开。调用方核对路径不越出根、文件存在且版本适用，不执行头文件内容；Schema 校验数组形状，不保证本机文件存在。Runtime 不复用 Ascend C 的包根假设。
- 文档归档 API 使用 `adv_api/`、`aicpu_api/`、`basic_api/`、`c_api/`、`simt_api/`、`tensor_api/`、`utils/` 下的公开 `.h` 路径，并统一补全 `include/` 前缀；路径不得含绝对路径、空段、`.`、`..` 或反斜杠。聚合兜底头（如 `kernel_operator.h`）不作为具体 API 的头文件定位信息。
- 值优先来自源文档正文的「头文件路径为：」声明与 `#include "..."`。缺少明确路径时，可依据固定版本源码审阅补充；必须区分声明与调用、注释及同名符号，不能仅凭符号出现位置判定声明头文件。
- 文档归档不含 `include/` 源码树。重复同步从文档重算显式路径；没有显式路径时，保留同一 `primary` 文档来源卡片中已有的合法补充，不猜测新路径。归档校验仅验证这些补充的格式和来源绑定，不声称重新扫描或证明源码声明；来源版本升级时须重新审阅补充路径，路径字符串未变也不能视为已验证新版本。
- `source_headers` 不表达需要单独链接的库文件（`.so`/`.a`）。
