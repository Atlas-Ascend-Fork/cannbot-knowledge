# cannbot-knowledge Agent 工作约定

本文件约束在本仓工作的自动化 Agent。它只说明执行规则；仓库介绍见 `README.md`，人工贡献流程见 `CONTRIBUTING.md`，字段和路径的完整语义见 `governance/specs/`。

## 工作边界

- `knowledge/` 是唯一知识正文根，也是唯一 OKF Bundle root。不要在其他目录保存 CANN、DSL、API、算子、调试或优化事实，也不要在知识树内创建嵌套 Bundle。
- `knowledge/` 中除 `index.md` 外的 Markdown 都是 OKF Concept document；Frontmatter `type` 是其 OKF 类型。目录中的 `concepts/`、`apis/`、`runbooks/` 等名称是路径 Profile，两者不能混用。
- `.agents/skills/`、`governance/`、`evals/`、`logs/` 和可重建的 `artifacts/` 是生产、消费与治理设施，`docs/` 与 `recipes/` 是说明和实践文档；它们都不属于 OKF Bundle。
- `docs/` 只解释设计原则和使用方式，`recipes/` 只提供场景化最佳实践。不要在两者中保存 CANN、DSL、API、算子、调试或优化事实，也不要把 Recipe 写成新的强制规则。
- 只修改当前任务需要的文件。开始前检查工作区，保留用户已有修改；不要顺手格式化或重写无关内容。
- 未经用户明确要求，不执行 commit、push、merge、tag、release、发布或修改用户全局环境。

## 维护本文件

- 每次修改仓库定位、目录结构、机器契约、知识生产/消费流程、质量门禁或 Skill 契约后，都要在交付前重新检查本文件。若现有指令已过时，必须在同一变更中同步更新。
- 本文件只保留跨任务、可长期执行的仓库约束。一次性状态、具体 Skill 脚本命令和容易变化的实现细节应分别进入当天日志、对应 `SKILL.md` 或 `references/`，不要在这里堆积。

## 规则从哪里读取

机器规则由下列事实源共同组成，不存在一份可以覆盖其他文件的“最高优先级”规则：

| 规则 | 唯一机器事实源 |
|---|---|
| 字段白名单、数据类型、数组形状和基础枚举 | `governance/schemas/frontmatter.schema.json` |
| 八个公共必选字段、路径 Profile 到 OKF `type` 的映射、Profile 字段组合 | `governance/schemas/profiles.yaml` |
| domain、route、platform、tag、受控附加路径值和固定归档本地来源 | `governance/schemas/registries.yaml` |
| 路径推导、跨字段/文件关系、索引和链接 | `governance/contracts/` |

`governance/specs/` 解释这些规则的语义和边界：修改知识卡重点阅读 `paths.md` 与 `frontmatter.md`；修改机器规则阅读 `schemas.md`；修改 Bundle/OKF 行为阅读 `okf.md`；修改 Skill 阅读 `skills.md`。目标目录的 `index.md` 提供当前内容导航。

Schema、Profile、Registry、Contract、Spec、Skill 或测试若互相矛盾，不要自行选择其中一份绕过。先定位唯一事实源，再在同一变更中修正执行逻辑、文档和回归。

## 修改知识卡

1. 先用 `knowledge-query` 搜索同一主题，阅读候选卡和来源，再明确采用 create、update、merge、split、deprecate 或 defer。不要只因标题不同就新建卡片，也不要自动覆盖已有卡片。
2. 按 `governance/specs/paths.md` 选择 domain、technology/scope 和路径 Profile。算子知识必须区分 DSL；只有真正不依赖单一技术实现的结论才能进入 `shared/`，跨技术映射进入同领域的 `shared/interoperability/`。
3. 按 `governance/specs/frontmatter.md` 填写字段。不要重复写可从路径推导的 domain、route、Profile 或 Concept ID，也不要为单张卡临时增加字段、标签或注册值。
4. `draft` 的 `sources` 可以为空，非 Glossary 的 `platforms` 也可以为空，但这些必选字段不能省略；轨迹沉淀的 `Runbook` 可使用 `sources: []`，但正文必须保留与结论强度相匹配的触发、探针、原始观测和验证信号；其他 `stable` 和 `deprecated` 必须有可核验来源。非 Glossary 还必须有明确平台范围。已知 Git 文件或目录来源必须固定到 40 位 commit；GitCode/GitHub PR 与 Issue 使用其规范工作项 URL；本地来源必须位于 Registry 登记根目录，固定归档获取脚本必须存在且可执行。
5. `status` 表示生命周期，`verified` 表示真实发生的复核事件，两者相互独立。不要因来源固定、Lint 通过或卡片进入 `stable` 而伪造 `verified`；`replaced_by` 只允许出现在 `deprecated` 卡片中，用于指向当前替代 Concept。
6. 正文应蒸馏可复用结论，并说明适用条件、失效边界和验证方式。不要大段复制来源，也不要把搜索摘要、聊天记录或模型记忆作为唯一技术证据。正文图片使用带 40 位 commit 和具体文件路径的 HTTPS Git raw URL，不提交本地图片副本或引用分支地址。
7. 新增、删除或移动卡片时同步受影响的每一级 `knowledge/**/index.md` 和正文链接。移动会改变 Concept ID，还必须同步所有 `replaced_by` 引用。
8. 实质知识变更按“日志”一节记录；纯排版和错别字修复不记日志。

## 目录与导航

- 文件名使用小写 `snake_case`，自由主题的集合目录使用复数；Registry 控制的 Operator 源码分类保持其注册 ID。五个 domain 根目录必须保留 `index.md`；只有 `ops` 和 `model` 预建注册 route，其他领域的下一层目录随首张真实知识创建。
- Operator 和 Runbook 只能使用 Registry 中声明的附加层级；`concepts`、`apis`、`examples`、`guides` 和 `optimizations` 可增加小写 `snake_case` 主题层级，其他路径 Profile 默认直接放卡片。
- `index.md` 只存在于 `knowledge/`。每个目录都必须有一个索引，完整且无重复地列出直接子目录和直接知识卡，并为每项提供摘要；domain 根和 `ops`/`model` 预建 route 可只有 index，且不表示已有知识覆盖。
- 只有 `knowledge/index.md` 声明 `okf_version: "0.2"`，其他索引不带 Frontmatter，所有索引均不参与知识检索。
- 知识卡和索引中的本地 Markdown 链接必须解析到 `knowledge/` Bundle 内的现有文件。图谱从通过 Contract 的卡片、逐层 Index、人工链接和本地 Agent 判定状态构建；候选召回不能直接成边，词法规则和节点度数也不能代替 Agent 判定。全量关系构建必须由多个 subagent 分片阅读正文，聚合器只做覆盖、指纹、类型和一致性校验。候选、review、冲突裁决、判定缓存、完整图谱和可视化全部保存在 ignored 的 `artifacts/graphs/`，不得提交；知识卡内由判定缓存派生的 `cannbot:related` 受管导航块可以提交，但不是技术事实源，也不进入 Query 语料。

## 修改治理和文档

- 先修改规则所属的唯一机器事实源，再同步受影响的 Contract、知识卡、Skill、Spec、正反测试和检索回归；不要在某个消费者里增加局部例外。
- 新字段、新注册值和新规则必须有稳定语义、实际消费者以及至少一个接受案例和一个拒绝案例，不能只为当前样例或未来占位而增加。
- 五份治理 Spec 分别负责 OKF、路径、Frontmatter、机器契约和 Skill。内容能并入现有职责时不要新建碎片化 Spec。
- 仓库级文档只描述当前仓库的定位、能力、语义和边界，不记录其他仓库的迁移过程，也不宣称尚未实现的能力。
- 根 `README.md` 直接维护 `docs/` 和 `recipes/` 的文档导航；`index.md` 仍然只用于 `knowledge/`。新增、删除或移动文档时同步根入口。
- Recipe 使用任务式名称，包含适用范围、预期产物、验证方式和失败/停止条件；它可以引用规则和 Skill，但不能复制规则定义或 Skill 内部接口。
- Skill 的脚本、参数和内部运行方式只写在对应 `SKILL.md` 或 `references/`；README、贡献指南和治理 Spec 只说明 Skill 本身及其输入输出边界。
- 实质治理或 Skill 契约变更按“日志”一节记录；纯排版和错别字修复不记日志。

## 修改 Skill

- 当前维护 `knowledge-ingest`、`knowledge-query`、`knowledge-lint` 三项基础 Skill、知识仓内的 `ops-knowledge-trace-ingest`（trace → runbooks 生产），以及 `ops-knowledge-vv-ingest`、`ops-knowledge-cv-ingest` 两项源码级 Operator producer。新增其他 Skill 仍需证明现有职责无法承载并完成架构评审。
- `.agents/skills/` 是本仓 Skill 的规范源。Skill 的实现、说明、参考资料和测试都在本仓维护与验证。
- Skill 保存生产、查询和治理知识的工作流、工具及必要的小型参考资料；可被复用的技术事实必须写入 `knowledge/`。Ingest 图谱流程只能同步明确标记的受管关系块，不得改动其他人工正文。
- `consumer` 和 `contributor` 是安装模式，不是路径 Profile、OKF `type` 或知识分类。
- 修改 Skill 时同步更新其 `SKILL.md`、`references/`、确定性实现和测试。规范源保持 Agent 平台中立，不在 Skill 内保存 `agents/openai.yaml` 等单一客户端元数据；客户端适配由本仓安装器在 Skill 外处理。

## 日志

- 实质知识、治理或 Skill 契约变更必须写入当天 `logs/YYYY-MM-DD.md`；日志只记录已经发生的操作和结果，不充当规则事实源或待办列表。
- 写日志前读取系统时钟，例如 `date '+%Y-%m-%d %H:%M'`。文件日期和条目 `[HH:MM]` 必须来自同一次读取，不得凭上下文猜测、使用未来时间或补造时间。
- 当天日志按时间倒序排列，最新条目放在文件顶部；保留已有历史条目，不为整理措辞而改写过去记录。
- 条目使用 `## [HH:MM] <operation> | 标题`、`### Summary` 和 `### Details`。纯排版、空白或错别字修复不记日志。

## 验证与交付

- 知识变更至少完成全库 Lint，并用一个与目标场景一致的查询验证召回；新增、删除或移动卡片不能只做单卡检查。
- 治理规则变更必须覆盖接受与拒绝行为；Query 行为变更必须覆盖过滤、排序或失败关闭语义。
- Skill 变更必须验证结构、正常路径、错误路径和权限边界。图谱流程还必须验证多个 Agent review 完整覆盖、重复运行幂等、缓存 stale 失败关闭、未声明或指纹不匹配的候选外关系拒绝、Agent 显式发现可接入、无图谱 degree 上限、边端点/类型、父索引闭包、受管关系块与缓存一致且注入幂等，以及除关系块外的人工正文不变和全部图谱产物位于 ignored 目录。
- 所有变更在交付前运行 `bash check.sh`。
- 最终说明实际修改的文件、关键语义变化、运行过的检查及结果；未执行或失败的检查要明确说明原因。
