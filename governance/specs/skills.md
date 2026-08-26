# Knowledge Skills

本仓维护 `knowledge-query`、`knowledge-ingest`、`knowledge-lint` 三项基础 Skill，以及 `ops-knowledge-vv-ingest`、`ops-knowledge-cv-ingest` 两项源码级 Operator producer。技术事实始终属于 `knowledge/`；Skill 保存生产、消费和治理这些事实的方法，不保存另一份领域知识。

具体执行接口只在各 Skill 自身的 `SKILL.md` 和 `references/` 中维护，本页只定义仓库级行为与协作边界。

## 分工

| Skill | 输入 | 输出 | 写入边界 |
|---|---|---|---|
| `knowledge-query` | 技术问题、decision、目标平台和可选范围条件 | 实际覆盖、候选 OKF Concept 或 search/ready/outcome receipt | 只读；只在调用方指定路径创建新审计产物 |
| `knowledge-ingest` | 固定来源、变化类型、目标路径、待表达结论和当前知识语料 | 路由决策、候选 Concept、Git 来源账本；可提交的受管关系块；ignored 的关系候选、判定缓存和本地图谱 | 可以创建候选卡并同步受管关系块；图谱 JSON 等产物不提交、不发布 |
| `knowledge-lint` | 单卡、完整知识仓或问题材料 | 分级确定性 Finding 报告或可复现 Issue 草稿 | 只读 |
| `ops-knowledge-vv-ingest` | 固定版本源码、唯一逻辑算子、入口、平台和独占目标文件 | 不含可达 Cube/AIC 或 MIX_CV 节点的源码级 Operator 卡 | 只写任务指定的最终卡 |
| `ops-knowledge-cv-ingest` | 固定版本源码、唯一逻辑算子、入口、平台和独占目标文件 | 含可达 Cube/AIC 或 MIX_CV 节点的源码级 Operator 卡 | 只写任务指定的最终卡 |

典型贡献流程是先 Query 查重；通用来源由 Ingest 形成候选卡，源码级完整算子由 VV/CV 中唯一匹配执行族边界的 producer 直接写目标卡；随后执行全库 Lint，最后用目标条件验证新卡可以被 Query 召回。只读问答不需要执行完整流程；人工编辑已有卡也可以不用创建能力，但仍应查重、Lint 和验证召回。

## Query

Query 是 CANNBot Profile 的专用、确定性、只读 consumer。索引构建器先按统一 Contract 校验全部 Concept，再把卡片、词项、行数和指纹原子写入 ignored 的 `artifacts/indexes/`。日常 Query 只消费经过校验的持久化索引，并对卡片集合、时间戳和治理指纹执行 stale check；完整校验还会从知识卡重新推导 document/posting 行，并继续使用同一只读连接。索引缺失、损坏、查询表不一致或内容陈旧时失败关闭，不临时扫描全库或静默重建。

它提供两类能力：

- **覆盖发现**：统计实际存在的 domain、technology/scope、OKF `type`、路径 `profile` 和 `status`；domain 根、`ops`/`model` 的 index-only route 和 Registry 中没有 Concept 的分类不计入覆盖。
- **知识搜索**：先执行结构化过滤，再做确定性词法评分，返回需要继续打开和核验的候选卡。

主要过滤语义：

| 条件 | 行为 |
|---|---|
| domain、profile、status | 精确匹配；默认只返回 `stable` |
| task、`tags` | task 规范化为 `task.*`；多个条件使用 AND |
| technology/scope | 默认只匹配所选 route 的专属卡 |
| shared | 只有显式要求时附加所选技术同领域的 shared 卡，不放宽到其他 DSL |
| platform | 普通搜索必须显式提供并包含全部目标平台；`agnostic` 卡可匹配任一已注册目标平台 |
| source/target technology | 精确匹配 `Interoperability` 端点 |

Profile 过滤使用目录 ID，例如 `apis`；结果同时返回 OKF `type: API` 和 `profile: apis`。`platforms: []` 不能满足平台过滤；只有显式未定位 draft 查询才能返回。Glossary 不携带平台字段，按平台中立术语处理。平台识别可在 `platforms` scope 中暂不传目标平台，其他搜索不得通过省略平台扩大范围。

Query 当前不按 CANN 版本执行结构化过滤。卡片仍可记录 `cann_versions`，搜索结果仍可返回该字段；调用方读取正文后自行核对版本边界。

文本评分按标题、摘要、`tags`/`aliases` 和正文递减加权，并使用 `verified` 事件派生信任层级：

- 无事件：`unverified`；
- 只有非 `human:` actor：`machine-confirmed`；
- 至少一个 `human:` actor：`human-reviewed`。

较低信任层级会降权，但不构成访问控制。结果中的摘要和最多两个来源只是选择线索；调用方必须打开 `local_path` 阅读正文、范围和完整来源。零命中只说明当前条件下未召回，不证明技术能力不存在。

搜索输出绑定 schema、完整请求、canonical 请求指纹、语料/治理指纹、仓库状态、行数和卡片 SHA-256。复杂任务按 decision 原子保存不可覆盖 search receipt；随后冻结 retrieval state，要求每条 receipt 与 state 使用完全相同的目标平台集合，核对完整索引 provenance，并按原请求重放过滤、评分、排序和命中。在全部 decision covered 后生成绑定每个 search receipt 文件 SHA-256 的 ready receipt，并用 outcome manifest 将未被修改的检索链、目标平台实验及产物 SHA-256 绑定到原 decision。

## Ingest

Ingest 是所有摄入请求的唯一入口，把可核验材料蒸馏成候选 Concept，不批量镜像上游内容，不保存中间推理。

1. 先区分 Git 与 Registry 登记的固定归档；Git 再按首次接入、同 ref 增量或版本升级路由，固定归档直接读取恢复后的来源；未迁移 producer 明确 defer。
2. Query 查重，决定 create、update、merge、split、deprecate 或 defer。
3. 选择 domain、technology/scope 和路径 Profile；Profile 自动决定 OKF `type` 和允许字段。
4. 固定并完整读取来源，区分来源事实、合理推导和待验证假设。
5. 将结论、适用范围、失败边界和验证方法写入正文，不复制大段上游内容。
6. 新卡默认 `draft`；只有来源、范围和正文满足消费门槛后才使用 `stable`。
7. 写入前调用统一 Contract，并用排他原子创建拒绝覆盖已有卡。
8. 创建后由贡献者更新索引和当天日志。
9. 知识批次完成后执行多通道宽候选召回和稳定分片，由多个独立 subagent 阅读 focal 与 shortlist 候选的完整正文后判定关系；shortlist 只减少无效阅读，Agent 可以用目标卡指纹明确提交正文中发现的候选外关系。聚合器只消费完整 Agent review，不以词法规则、分数阈值或节点度数自动定边；Agent 对同一 pair 的关系类型冲突必须交给一个或多个 Agent 阅读全文裁决，多个裁决分片必须互不重叠且合并后完整覆盖冲突集。
10. 将接受关系同步为知识卡中可提交的 `cannbot:related` 受管导航块，再执行全库 Lint，重建 Query 索引并运行目标 Query；候选、review、裁决、判定缓存、完整图谱和可视化始终留在 ignored 的 `artifacts/graphs/`，Query 不索引受管关系块。

Git Reference 批次使用 inventory、ledger 和不可覆盖 receipt；固定归档批次以 Registry 中的 archive SHA-256 固定来源，直接执行查重、蒸馏和建卡，不生成这三类批次产物。固定归档切换到新 archive SHA-256 的流程尚未实现，必须 defer。

`verified` 只在掌握真实 actor 和时间时填写。固定来源或创建成功不自动产生验证事件。Interoperability 必须位于同领域 `shared`，并声明两个不同的已注册技术端点。

本地图谱包含通过 Contract 的 Concept 与 Index、由目录派生的 `part_of`、人工正文的 `links_to`，以及 Agent 判定缓存接受的 `exemplifies`、`explains`、`same_topic` 和 `related`。候选、review 分片、冲突裁决、已接受关系及其卡片指纹、理由、Agent 身份、强度、置信度、证据、完整图谱和可视化全部写入 ignored 的 `artifacts/graphs/`。受管关系块是这些判定在知识卡中的可提交导航投影，不是人工正文或技术事实源；技术回答仍以卡片正文和来源为准。

图谱候选、判定缓存、构建和可视化产物不提交，也不是独立知识真值。候选分数和召回通道只能帮助 subagent 定位阅读顺序；版本和平台用于 Agent 判断适用边界，不作为候选过滤器。判定缓存必须由至少两个 subagent 覆盖当前全部 focal，并通过语料、分片和卡片指纹校验。Ingest 只能改写受管关系块，且必须保证注入幂等、链接可解析、块外人工正文不变。

## Operator producer

两项 Operator producer 处理通用 Ingest 无法用固定模板闭合的源码级 API/Host/Tiling/Kernel 事实。任务必须先冻结唯一逻辑算子、固定 Git Commit、入口类型、平台和目标文件；入口可以是公开 ACLNN/API、官方 Host/Tiling 或 Direct Invoke，Skill 不自行改变调用层。

分流只看 Host/launcher 可达的 Device 节点：全部节点都不含 Cube/AIC 或 MIX_CV 时使用 VV；至少一个节点含 Cube/AIC 或 MIX_CV 时使用 CV。SIMT、NDDMA、通信、Hybrid 和多 Kernel 本身不触发 CV。两项 Skill 都必须闭合公开入口或 launcher、Host selector、Tiling/POD、逐 Route Kernel、内存、同步、构建接线和固定来源；闭包或公开平台证据不足时停止写正式卡。

producer 一次只处理一个逻辑算子并只写任务指定的最终卡，不写 index、Registry、日志、图谱或中间账本，不执行编译、真机、数值或性能测试。外层贡献流程负责查重、导航、日志、Lint、索引和目标 Query。两项 producer 的固定标题、Frontmatter 和正文结构由各自模板定义。

## Lint

Lint 是离线、只读、确定性的作者门禁，比 OKF 最小 conformance 更严格。

| 范围 | 检查内容 |
|---|---|
| OKF/CANNBot Profile | 根版本、YAML mapping 唯一 key、非空 `type`、路径 Profile 映射、JSON Schema 和字段白名单 |
| 路径与受控值 | domain-route、附加层级、文件名、platform、Tag、技术端点 |
| 生命周期与来源 | `status`、有效日历时间、`verified` actor、`replaced_by`、来源形状、Git 文件 commit 固定格式与 GitCode/GitHub PR/Issue URL；本地来源获取脚本存在且可执行，已恢复来源的归档标记和在用文件存在 |
| 导航、正文与日志 | domain 根和 `ops`/`model` route 骨架完整；每层索引列出直接子项；行内/显式引用式 Markdown 目标是 Bundle 内的现有文件；图片使用固定 commit 的 Git raw 文件 URL；正文非空且无 Git 冲突标记；日志格式、必需 section 与倒序正确 |

单卡检查不覆盖父级索引和完整目录树；新增、删除或移动文件后必须执行全库检查。统一门禁启用严格来源导航，要求宽 Git tree 来源由同仓库、同 revision 的 blob 来源或正文链接定位。Lint 只确认链接目标和 Bundle 边界，不验证 Markdown 锚点。

Lint 不联网检查 URL，不判断来源是否充分、正文是否正确、实验能否复现、shared 泛化是否合理或跨 DSL 是否等价。Registry 本地来源根不存在时不要求联网恢复；存在时才核对 archive SHA-256 完成标记和被引用文件。Lint 固定执行自身版本的 Contract，目标根 Contract 不一致时失败，不导入目标根 Python。结构通过不等于结论正确。知识内容、检索、图谱、编译、治理或下游使用问题的材料整理也由 Lint 承载；它只生成本地 Issue 草稿和 `needs-info`，不会自行向外部系统提交。

## 共同约束

- 五项 Skill 共同遵守 `governance/schemas/` 和 `governance/contracts/`，不复制或放宽字段、路径和注册值。
- 五项 Skill 的可移植合同由 `SKILL.md` 的 `name`、`description` 和正文，以及按需加载的 `references/`、`templates/`、`scripts/` 等资源组成。规范源不保存 `agents/openai.yaml` 或其他单一 Agent 平台元数据。
- Query 和 Lint 始终只读；Ingest 不自动 commit、push、合并或发布。
- CANN、DSL、API、算子、调试和优化事实进入 `knowledge/`，不埋在 Skill 指令中。
- 官方 reference 来源盘点与通用摄入路由属于 Ingest，源码级完整算子生产属于 VV/CV，Issue 材料整理属于 Lint。其他专用 producer 需要单独完成架构和发布评审。

## 安装模式

| 安装模式 | Skill | 场景 |
|---|---|---|
| `consumer` | `knowledge-query` | 只读查阅和技术问答 |
| `contributor` | 全部五项 Skill | 贡献知识、治理规则或 Skill |

知识仓安装入口把平台中立的规范源链接到目标项目 `.agents/skills/`，再在 Skill 目录之外创建客户端适配链接；同时准备索引、写项目级知识根配置并维护 Agent 提示词入口。复制式安装必须另行配置知识根。两种方式都要求知识仓独立可用，不复制 `knowledge/` 正文或修改用户全局配置。

知识正文、机器规则、Contract 和 Skill 规范源都以本仓 Git commit 标识。
