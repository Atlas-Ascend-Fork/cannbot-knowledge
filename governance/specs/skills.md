# Knowledge Skills

本仓维护 `knowledge-query`、`knowledge-ingest`、`knowledge-lint` 三项基础 Skill，Ascend C API 专用消费流程 `ascendc-api-knowledge-query`，仓内专用的 `ops-knowledge-trace-ingest`，以及 `ops-knowledge-vv-ingest`、`ops-knowledge-cv-ingest` 两项源码级 Operator producer。技术事实始终属于 `knowledge/`；Skill 保存生产、消费和治理这些事实的方法，不保存另一份领域知识。

具体执行接口只在各 Skill 自身的 `SKILL.md` 和 `references/` 中维护，本页只定义仓库级行为与协作边界。

## 分工

| Skill | 输入 | 输出 | 写入边界 |
|---|---|---|---|
| `knowledge-query` | 技术问题、decision、目标平台和可选范围条件 | 实际覆盖、候选 OKF Concept 或 search/ready/outcome receipt | 只读；只在调用方指定路径创建新审计产物 |
| `ascendc-api-knowledge-query` | Ascend C API 问题、硬件平台和按需提供的本地 CANN 包路径 | 经平台过滤和全文核验的 API 结论、相关卡片及头文件证据/缺口 | 只读；检索和审计委托 Query |
| `knowledge-ingest` | 固定来源、变化类型、目标路径、待表达结论和当前知识语料 | 路由决策、候选 Concept、Git 来源账本；可提交的受管关系块；ignored 的关系候选、判定缓存和本地图谱 | 可以创建候选卡并同步受管关系块；图谱 JSON 等产物不提交、不发布 |
| `knowledge-lint` | 单卡、完整知识仓或问题材料 | 分级确定性 Finding 报告或可复现 Issue 草稿 | 只读 |
| `ops-knowledge-trace-ingest` | 本仓可读的算子开发 trace、日志或已归一化事件流 | 经证据门禁、独立审查和全库图谱收口的 Ascend C Runbook | 只在本知识仓使用；只写经审查卡、导航和日志 |
| `ops-knowledge-vv-ingest` | 固定版本源码、唯一逻辑算子、入口、平台和独占目标文件 | 不含可达 Cube/AIC 或 MIX_CV 节点的源码级 Operator 卡 | 只写任务指定的最终卡 |
| `ops-knowledge-cv-ingest` | 固定版本源码、唯一逻辑算子、入口、平台和独占目标文件 | 含可达 Cube/AIC 或 MIX_CV 节点的源码级 Operator 卡 | 只写任务指定的最终卡 |

典型贡献流程是先 Query 查重；通用来源由 Ingest 形成候选卡，本仓内的开发 trace 由 Ingest 路由到 trace producer，源码级完整算子由 VV/CV 中唯一匹配执行族边界的 producer 直接写目标卡；随后执行全库 Lint，最后用目标条件验证新卡可以被 Query 召回。只读问答不需要执行完整流程；人工编辑已有卡也可以不用创建能力，但仍应查重、Lint 和验证召回。

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

Profile 过滤使用目录 ID，例如 `apis`；结果同时返回 OKF `type: API` 和 `profile: apis`。`platforms: []` 不能满足平台过滤；只有显式未定位 draft 查询才能返回。精确 API 名在目标平台 stable 查询零命中时，调用方必须另发一次不带 platform 的 `--include-unlocated --status draft` 查询，并把命中标为平台待核验候选，不能混入原平台结果或写进同一审计 receipt。Glossary 不携带平台字段，按平台中立术语处理。平台识别可在 `platforms` scope 中暂不传目标平台，其他搜索不得通过省略平台扩大范围。

Query 当前不按 CANN 版本执行结构化过滤。卡片仍可记录 `cann_versions`，搜索结果仍可返回该字段；调用方读取正文后自行核对版本边界。

文本评分按标题、摘要、`tags`/`aliases` 和正文递减加权，并使用 `verified` 事件派生信任层级：

- 无事件：`unverified`；
- 只有非 `human:` actor：`machine-confirmed`；
- 至少一个 `human:` actor：`human-reviewed`。

较低信任层级会降权，但不构成访问控制。Agent 先依据脚本返回的路径、title 和 description 选择候选，再打开选中卡片的 `local_path` 阅读完整正文、范围和来源；读完后由 Agent 决定是否沿有效链接继续阅读相关知识或 include，不要求读取全部命中及链接。零命中只说明当前条件下未召回，不证明技术能力不存在。

搜索输出绑定 schema、完整请求、canonical 请求指纹、语料/治理指纹、仓库状态、行数和卡片 SHA-256。复杂任务按 decision 原子保存不可覆盖 search receipt；随后冻结 retrieval state，要求每条 receipt 与 state 使用完全相同的目标平台集合，核对完整索引 provenance，并按原请求重放过滤、评分、排序和命中。在全部 decision covered 后生成绑定每个 search receipt 文件 SHA-256 的 ready receipt，并用 outcome manifest 将未被修改的检索链、目标平台实验及产物 SHA-256 绑定到原 decision。

## Ascend C API 专用消费

`ascendc-api-knowledge-query` 是显式可调用的专业流程，负责通用 Query 之外的全文阅读、按问题追踪多跳关系，以及将 API 卡的 `source_headers` 相对路径解析到已确认的 AscendC 包根。它依赖并复用 Query 的检索、平台识别、索引和审计，不引入第二份检索实现、SDK 索引或 API 事实库；与 Query 同装，避免独立安装缺少底层能力。通用 API 选择模式仍服务其他技术，Ascend C 场景无需重复执行两套流程。

硬件平台先于普通 API 查询确定；相关卡片仍需独立核对范围。已选卡片的本地来源、相对链接和 include 使用只读路径解析，复用 Query 的知识根与既有来源 Contract；解析结果不是已读正文或已验证版本，不扫描源码树寻找替代证据。头文件只在正文不足以回答当前问题时按需读取，实际包版本与文档来源版本必须区分；头文件存在或调用导航不能单独证明平台支持。缺失、冲突或越界保持未确认，消费流程不修改或安装 SDK。

所选卡片的分页阅读保持原文、原始行号和内容指纹，不用摘要代替正文；遇到内容变化要求重新阅读。完成当前页的边界和续读位置在正文之后返回，避免截断前缀仍预告可跳过的范围。页码或文件末尾标志只描述本次返回范围，不是 Agent 已读完整卡片或证据足以支持结论的证明。分页不新增检索、平台豁免或审计状态，也不修改知识文件。

已选卡片之间的字段对照只提供原文上下文，排除 Frontmatter 和受管导航，不搜索其他卡片。对照片段不替代完整阅读，不自动裁决技术冲突；范围和单位的采用判断仍由 Agent 负责。

交付前，消费 Agent 以已读证据复核拟采用的技术判断，区分原文支持的约束和额外推断，并处理跨来源冲突。复核不增加写入权限、自动委派或全库重读要求；最终答复与“已完成阅读”是分别需要核验的结果。

## Ingest

Ingest 是所有摄入请求的唯一入口。通常把可核验材料蒸馏成候选 Concept；Registry 固定归档中的官方 API/Guide 按声明执行导航页过滤、冗余章节省略和其余正文保留。两种模式都不保存中间推理。

1. 先区分 Git 与 Registry 登记的固定归档；Git 再按首次接入、同 ref 增量或版本升级路由，固定归档直接读取恢复后的来源；未迁移 producer 明确 defer。
2. Query 查重，决定 create、update、merge、split、deprecate 或 defer。
3. 选择 domain、technology/scope 和路径 Profile；Profile 自动决定 OKF `type` 和允许字段。
4. 固定并完整读取来源，区分来源事实、合理推导和待验证假设。
5. 通常将结论、适用范围、失败边界和验证方法写入正文，不复制大段上游内容；固定归档 API/Guide 不为纯导航页建卡，以逐层 `index.md` 作为唯一目录入口。保留页只省略 Registry 声明的冗余章节、增加 Frontmatter、改写失效链接目标并同步受管关系块；“产品支持情况”只进入 `platforms`。
6. 新卡默认 `draft`；只有来源、范围和正文满足消费门槛后才使用 `stable`。
7. 写入前调用统一 Contract，并用排他原子创建拒绝覆盖已有卡。
8. 创建后由贡献者更新索引和当天日志。
9. 一般语义关系在知识批次完成后执行多通道宽候选召回和稳定分片，由多个独立 subagent 以小批次阅读 focal 与 shortlist 候选的完整正文后判定；shortlist 只减少无效阅读，Agent 可以用目标卡指纹明确提交正文中发现的候选外关系。未明确决定表示 abstain；完整阅读后确认的近似误召回可显式拒绝。聚合器只消费完整 Agent review，不以词法规则、分数阈值或节点度数自动定边；同一 pair 的接受/显式拒绝冲突或关系类型冲突必须交给未参与原判定的 Agent 阅读全文裁决，多个裁决分片必须互不重叠且合并后完整覆盖冲突集，聚合失败不得继续复用旧缓存。固定归档 API→Operator 的“明确调用”是可机械复验的语法证据，不作为一般语义推断：强命名空间或成员接收者必须在平台和参数数量过滤前、面向完整同名卡集合唯一识别 API，平台和参数数量只排除不兼容候选，不证明家族或方向；同名多卡的无归属调用必须 abstain。Registry 以大小写与分隔符不敏感方式排除 `Init`、`size`、`min` 等无法证明具体自由函数或成员方法归属的泛化符号。图谱注入更新 API 端的一般语义关系时必须原样合并自动关系子区块，不能跳过该端或覆盖自动边。
10. 将接受关系同步为知识卡中可提交的 `cannbot:related` 受管导航块，再执行全库 Lint，重建 Query 索引并运行目标 Query；候选、review、裁决、判定缓存、明确调用审计、完整图谱和可视化始终留在 ignored 的 `artifacts/graphs/`，Query 不索引受管关系块。即使本地没有一般语义判定缓存，也必须合成并校验包含结构关系与明确 API 调用边的图谱，不得静默跳过。

Git Reference 批次使用 inventory、ledger 和不可覆盖 receipt；固定归档批次以 Registry 中的 archive SHA-256 固定来源，直接执行查重、受控转换或蒸馏建卡，不生成这三类批次产物。固定归档升级时先记录旧/新 SHA-256 并审查完整结构 diff，更新 Registry 后重新通过获取脚本校验，完成卡片、导航、关系、Lint 和 Query 后才记录完成。

`verified` 只在掌握真实 actor 和时间时填写。固定来源或创建成功不自动产生验证事件。Interoperability 必须位于同领域 `shared`，并声明两个不同的已注册技术端点。

自动 API→Operator 关系在知识更新与完整门禁中优先验证算子卡声明文件中的固定提交源码调用，源码未恢复或 checkout 被修改时失败关闭；只在声明文件范围内做语法检查，不证明运行时可达性。仅有卡片正文证据的调用另行标注。普通构图与 CI 消费已提交的自动导航，校验区块结构、端点、关系类型、重复项、展示上限及源码链接的登记提交和算子来源归属，不下载或重新扫描源码，也不把导航校验当作调用证据复验。Registry 的正整数展示上限同时控制自动导航和对应图谱边，超出时注明“部分算子”，全部接受关系和源码行证据仍保存于 ignored 审计产物；此上限不限制一般语义边，也不是新的判定规则。

本地图谱包含通过 Contract 的 Concept 与 Index、由目录派生的 `part_of`、人工正文的 `links_to`，以及 Agent 判定缓存接受的 `exemplifies`、`explains`、`same_topic` 和 `related`。候选、review 分片、冲突裁决、已接受关系及其卡片指纹、理由、Agent 身份、强度、置信度、证据、完整图谱和可视化全部写入 ignored 的 `artifacts/graphs/`。受管关系块是这些判定在知识卡中的可提交导航投影，不是人工正文或技术事实源；技术回答仍以卡片正文和来源为准。

图谱候选、判定缓存、构建和可视化产物不提交，也不是独立知识真值。候选分数和召回通道只能帮助 subagent 定位阅读顺序；版本和平台用于 Agent 判断适用边界，不作为候选过滤器。判定缓存必须由至少两个 subagent 覆盖当前全部 focal，并通过语料、候选产物、分片和卡片指纹校验；语料或候选产物变化后必须失败关闭。每个接受或显式拒绝判定都必须用双方 Concept ID 为键，分别从去除受管关系块后的对应卡片正文逐字摘录具体事实，并明确桥接理由和范围；模板、截断、非正文锚点或自相矛盾的证据失败关闭。Ingest 只能改写受管关系块，且必须保证注入幂等、链接可解析、块外人工正文不变，校验同时覆盖 JSON 与 HTML 图谱产物。

本地门禁与 CI 使用同一份完整图谱构建实现，统一校验知识节点、逐层索引和受管关系；不得以只读取显式链接的旧版图谱替代完整构图。

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
| 生命周期与来源 | `status`、有效日历时间、`verified` actor、`replaced_by`、来源形状、Git 文件 commit 固定格式与 GitCode/GitHub PR/Issue URL；本地来源获取脚本存在且可执行，已恢复来源的归档标记或 Git 提交/来源/工作区合法，在用文件存在 |
| 导航、正文与日志 | domain 根和 `ops`/`model` route 骨架完整；每层索引列出直接子项；行内/显式引用式 Markdown 知识导航目标是 Bundle 内的现有文件，知识卡另可引用登记的固定提交源码文件；图片使用固定 commit 的 Git raw 文件 URL；正文非空、围栏外恰有一个 H1（固定归档主来源 API/Guide 镜像可保留多个）、无 Git 冲突标记或压平表格；日志格式、必需 section 与倒序正确 |

单卡检查不覆盖父级索引和完整目录树；新增、删除或移动文件后必须执行全库检查。统一门禁启用严格来源导航，要求宽 Git tree 来源由同仓库、同 revision 的 blob 来源或正文链接定位。Lint 只确认链接目标和 Bundle 边界，不验证 Markdown 锚点。

Lint 不联网检查 URL，不判断来源是否充分、正文是否正确、实验能否复现、shared 泛化是否合理或跨 DSL 是否等价。Registry 本地来源根不存在时不要求联网恢复；存在时才核对 archive SHA-256 完成标记或 Git 固定提交、远程来源、干净工作区和被引用文件。Lint 固定执行自身版本的 Contract，目标根 Contract 不一致时失败，不导入目标根 Python。结构通过不等于结论正确。知识内容、检索、图谱、编译、治理或下游使用问题的材料整理也由 Lint 承载；它只生成本地 Issue 草稿和 `needs-info`，不会自行向外部系统提交。

## 共同约束

- 七项 Skill 共同遵守 `governance/schemas/` 和 `governance/contracts/`，不复制或放宽字段、路径和注册值。
- 七项 Skill 的规范合同由 `SKILL.md` 的 `name`、`description` 和正文，以及按需加载的 `references/`、`templates/`、`scripts/` 等资源组成。其中六项可由安装器链接到业务项目，trace producer 保持仓内运行。规范源不保存 `agents/openai.yaml` 或其他单一 Agent 平台元数据。
- Query 和 Lint 始终只读；Ingest 不自动 commit、push、合并或发布。
- CANN、DSL、API、算子、调试和优化事实进入 `knowledge/`，不埋在 Skill 指令中。
- 官方 reference 来源盘点与通用摄入路由属于 Ingest，仓内开发 trace 动态摄入属于 trace producer，源码级完整算子生产属于 VV/CV，Issue 材料整理属于 Lint。其他专用 producer 需要单独完成架构和发布评审。

## 安装模式

| 安装模式 | Skill | 场景 |
|---|---|---|
| `consumer` | `knowledge-query`、`ascendc-api-knowledge-query` | 只读查阅和技术问答 |
| `contributor` | 六项可安装 Skill（三项基础 + ascendc-api-knowledge-query + VV/CV） | 贡献知识、治理规则或 Skill；不包含仓内 trace producer |

知识仓安装入口把平台中立的规范源链接到目标项目 `.agents/skills/`，再在 Skill 目录之外创建客户端适配链接；默认恢复登记的文档和固定提交源码后准备索引（显式离线安装可跳过资源），写项目级知识根配置并维护 Agent 提示词入口。复制式安装必须另行配置知识根。两种方式都要求知识仓独立可用，不复制 `knowledge/` 正文或修改用户全局配置。

项目提示词只维护领域任务的触发、入口路由和消费边界；具体平台识别、补搜、阅读、来源核对及审计规则由对应 Skill 维护，不在安装器中复制第二套检索工作流。

知识正文、机器规则、Contract 和 Skill 规范源都以本仓 Git commit 标识。
