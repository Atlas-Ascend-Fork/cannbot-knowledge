# Knowledge Skills

本仓只维护 `knowledge-query`、`knowledge-ingest` 和 `knowledge-lint` 三项基础 Skill。技术事实始终属于 `knowledge/`；Skill 保存生产、消费和治理这些事实的方法，不保存另一份领域知识。

具体执行接口只在各 Skill 自身的 `SKILL.md` 和 `references/` 中维护，本页只定义仓库级行为与协作边界。

## 分工

| Skill | 输入 | 输出 | 写入边界 |
|---|---|---|---|
| `knowledge-query` | 技术问题、decision、目标平台和可选范围条件 | 实际覆盖、候选 OKF Concept 或 search/ready/outcome receipt | 只读；只在调用方指定路径创建新审计产物 |
| `knowledge-ingest` | 固定来源、变化类型、目标路径和待表达结论 | 路由决策、候选 Concept、来源账本；可重建本地图谱 | 可以创建候选卡和 ignored 产物，不覆盖已有知识卡、不提交、不发布 |
| `knowledge-lint` | 单卡、完整知识仓、Skill 镜像或问题材料 | 确定性错误报告或可复现 Issue 草稿 | 只读 |

典型贡献流程是先 Query 查重，再由 Ingest 形成候选卡，随后执行全库 Lint，最后用目标条件验证新卡可以被 Query 召回。只读问答不需要执行完整流程；人工编辑已有卡也可以不用创建能力，但仍应查重、Lint 和验证召回。

## Query

Query 是 CANNBot Profile 的专用、确定性、只读 consumer。索引构建器先按统一 Contract 校验全部 Concept，再把卡片、词项、行数和指纹原子写入 ignored 的 `artifacts/indexes/`。日常 Query 只消费经过校验的持久化索引，并对卡片集合、时间戳和治理指纹执行 stale check；索引缺失、损坏或陈旧时失败关闭，不临时扫描全库或静默重建。

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
| CANN version | 必须显式声明目标版本；字段缺失不代表全版本兼容 |
| source/target technology | 精确匹配 `Interoperability` 端点 |

Profile 过滤使用目录 ID，例如 `apis`；结果同时返回 OKF `type: API` 和 `profile: apis`。`platforms: []` 不能满足平台过滤；只有显式未定位 draft 查询才能返回。Glossary 不携带平台字段，按平台中立术语处理。平台识别可在 `platforms` scope 中暂不传目标平台，其他搜索不得通过省略平台扩大范围。

文本评分按标题、摘要、`tags`/`aliases` 和正文递减加权，并使用 `verified` 事件派生信任层级：

- 无事件：`unverified`；
- 只有非 `human:` actor：`machine-confirmed`；
- 至少一个 `human:` actor：`human-reviewed`。

较低信任层级会降权，但不构成访问控制。结果中的摘要和最多两个来源只是选择线索；调用方必须打开 `local_path` 阅读正文、范围和完整来源。零命中只说明当前条件下未召回，不证明技术能力不存在。

搜索输出绑定 schema、完整请求、canonical 请求指纹、语料/治理指纹、仓库状态、行数和卡片 SHA-256。复杂任务按 decision 原子保存不可覆盖 search receipt；随后冻结 retrieval state，重新校验 receipt 内外结构、请求指纹、证据和当前索引，在全部 decision covered 后生成绑定每个 search receipt 文件 SHA-256 的 ready receipt，并用 outcome manifest 将未被修改的检索链、目标平台实验及产物 SHA-256 绑定到原 decision。

## Ingest

Ingest 是所有摄入请求的唯一入口，把可核验材料蒸馏成候选 Concept，不批量镜像上游内容，不保存中间推理。

1. 先按首次接入、同 ref 增量或版本升级路由，再按来源类型选择已迁移 producer；未迁移 producer 明确 defer。
2. Query 查重，决定 create、update、merge、split、deprecate 或 defer。
3. 选择 domain、technology/scope 和路径 Profile；Profile 自动决定 OKF `type` 和允许字段。
4. 固定并完整读取来源，区分来源事实、合理推导和待验证假设。
5. 将结论、适用范围、失败边界和验证方法写入正文，不复制大段上游内容。
6. 新卡默认 `draft`；只有来源、范围和正文满足消费门槛后才使用 `stable`。
7. 写入前调用统一 Contract，并拒绝覆盖已有卡。
8. 创建后由贡献者更新索引和当天日志，再执行全库 Lint 与目标 Query。

`verified` 只在掌握真实 actor 和时间时填写。固定来源或创建成功不自动产生验证事件。Interoperability 必须位于同领域 `shared`，并声明两个不同的已注册技术端点。

本地图谱从通过 Contract 的 Concept 及其显式链接生成到 ignored 的 `artifacts/graphs/`。它可以随时重建，不是仓库真值。

## Lint

Lint 是离线、只读、确定性的作者门禁，比 OKF 最小 conformance 更严格。

| 范围 | 检查内容 |
|---|---|
| OKF/CANNBot Profile | 根版本、非空 `type`、路径 Profile 映射、JSON Schema 和字段白名单 |
| 路径与受控值 | domain-route、附加层级、文件名、platform、Tag、技术端点 |
| 生命周期与来源 | `status`、时间、`verified` actor、`replaced_by`、来源形状和 Git commit 固定格式 |
| 导航、正文与日志 | domain 根和 `ops`/`model` route 骨架完整；每层索引列出直接子项；Markdown 目标存在；正文无冲突/图片/占位；日志格式与倒序正确 |
| Skill 镜像 | 规范源与指定 Plugin 镜像的文件集合和内容一致 |

单卡检查不覆盖父级索引和完整目录树；新增、删除或移动文件后必须执行全库检查。Lint 只确认链接目标存在，不验证 Markdown 锚点。

Lint 不联网检查 URL，不判断来源是否充分、正文是否正确、实验能否复现、shared 泛化是否合理或跨 DSL 是否等价。结构通过不等于结论正确。知识内容、检索、图谱、编译、治理或下游使用问题的材料整理也由 Lint 承载；它只生成本地 Issue 草稿和 `needs-info`，不会自行向外部系统提交。

## 共同约束

- 三项 Skill 共同使用 `governance/schemas/` 和 `governance/contracts/`，不复制字段、路径或注册值。
- 三项 Skill 的可移植合同由 `SKILL.md` 的 `name`、`description` 和正文，以及按需加载的 `references/`、`scripts/` 等资源组成。规范源不保存 `agents/openai.yaml` 或其他单一 Agent 平台元数据。
- Query 和 Lint 始终只读；Ingest 不自动 commit、push、合并或发布。
- CANN、DSL、API、算子、调试和优化事实进入 `knowledge/`，不埋在 Skill 指令中。
- 官方 reference 来源盘点与摄入路由属于 Ingest，Issue 材料整理属于 Lint；它们不增加公开 Skill。其他专用 ingest producer 通过后续 PR 逐项接入统一路由。

## 安装模式与发布镜像

| 安装模式 | Skill | 场景 |
|---|---|---|
| `consumer` | `knowledge-query` | 只读查阅和技术问答 |
| `contributor` | 全部三个 Skill | 贡献知识、治理规则或 Skill |

知识仓安装入口始终把平台中立的规范源链接到目标项目 `.agents/skills/`，再在 Skill 目录之外创建客户端适配链接；同时准备索引、写项目级知识根配置并维护 Agent 提示词入口。Marketplace 从 Plugin 仓提供 consumer、contributor 和 Team 套件；复制式安装必须另行配置知识根。两种方式都要求知识仓独立可用，不复制 `knowledge/` 正文或修改用户全局配置。

`.agents/skills/` 是规范源，`cannbot-skills/plugins-community/cannbot-knowledge/skills/` 是完整发布镜像。Skill 先在规范源修改和验证，再完整同步镜像；镜像不得独立演进。

知识正文、机器规则、Contract 和 Skill 规范源以知识仓 Git commit 标识；Marketplace 套件和 Team Plugin 使用自己的 SemVer。知识变化不自动等于 Plugin 破坏性变更；只有 Skill 接口、安装入口或套件内容不再兼容时，才按 Plugin 规则提升相应主版本。正式发布应记录配套的知识 commit 与 Plugin 版本，并在两个仓库的 PR、tag 或 release notes 中互相引用。
