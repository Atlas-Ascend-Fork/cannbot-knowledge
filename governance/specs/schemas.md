# Schema、Registry 与 Contract

`governance/schemas/` 保存声明式机器规则，`governance/contracts/` 负责组合和执行这些规则。所有 YAML mapping 拒绝重复 key，避免解析时静默覆盖规则或卡片字段。Spec 解释语义和贡献边界，但不是另一套机器事实源。

## 唯一职责

| 文件 | 负责 | 不负责 |
|---|---|---|
| `schemas/frontmatter.schema.json` | OKF 与扩展字段白名单、数据类型、数组形状和基础枚举 | 不按路径 Profile 选择字段，不保存平台或标签词表 |
| `schemas/profiles.yaml` | 八个公共必选字段、Profile 到 OKF `type` 的映射、各 Profile 字段组合 | 不定义字段数据类型，不判断路径是否合法 |
| `schemas/registries.yaml` | domain、route、platform、标签、受控附加路径值，以及文档归档、固定提交 Git 本地来源与转换策略 | 不保存知识正文、逐卡来源、发布版本或变更历史 |
| `contracts/knowledge.py` | 加载声明并为 Ingest、Query 等消费者保留统一兼容门面 | 不重复实现各检查类别 |
| `contracts/checks/*.py` | 按路径、Profile、来源、图片、导航等类别实现确定性检查；`__init__.py` 静态注册检查及 P0–P2 等级 | 不保存 Schema、Profile 或 Registry 的平行枚举 |
| `contracts/indexes.py` | 生成并比较直接子项索引，供 Ingest 与 Lint 共用 | 不写文件，不决定 CI 展示 |

同一规则只能有一个机器事实源：字段形状归 JSON Schema，字段组合和 `okf_type` 归 Profile，受控值归 Registry，依赖路径、其他字段或其他文件的关系归 Contract。

顶层字段是否必选只由 `profiles.yaml` 的 `common_required` 与各 Profile `required` 声明。Frontmatter Schema 不重复顶层 `required`，但仍负责 `sources[].resource`、`verified.by/at` 等嵌套对象的必选字段。`title` 和 `description` 的字符串类型归 Schema，非空文本语义归 Profile 检查。

Contract 直接消费这些声明，只保留现有的可加载性和 `okf_type` 基础检查，不增加 required/optional 重复、交叉或 Schema 字段名单等 Profile 声明自校验层。

## Registry 分区

`registries.yaml` 是多个消费者共享的小型受控词表。“已注册”表示工具能识别，不表示 `knowledge/` 必须预建对应路径或已有 Concept。Contract 只强制 domain 根和 `ops`/`model` 的注册 route 作为协作骨架。

| 分区 | 保存内容 | 主要用途 |
|---|---|---|
| `domains` | 顶层领域、允许直辖的 `direct_types` 及是否 `precreate_routes` | 路径校验、domain 过滤、协作骨架 |
| `technologies` | DSL、语言、框架或引擎及允许的 domain | route、technology 和跨技术端点校验 |
| `scopes` | `shared`、平台、工具链、推理/训练等非技术 route | route、scope 和 shared 过滤 |
| `scope_schemas` | 场景 Scope namespace、适用路径、维度类型、值与别名 | 卡片适用条件校验及 Contract 三态比较；与路径 route 的 `scopes` 分区独立 |
| `paths` | Operator call mode、family→category 映射和 Runbook area | 受控附加层级校验 |
| `platforms` | 卡片适用平台 ID | Frontmatter 校验和 platform 过滤 |
| `tags` | task、topic、paradigm 三个维度的规范标签 | 标签校验、任务映射、过滤和召回 |

`local_sources` 以 `kind: git` 声明固定源码资源，包含安全的仓库相对 `root`、可执行 `fetch_script`、规范 `repository` 和非空、去重、排序的 40 位 `revisions`。Git 根可多级组织，根之间必须唯一且无祖先/后代重叠；规范仓库身份也不能重复，且不得使用知识或治理设施目录。

无 `kind` 或使用 `kind: archive` 时保持归档顶层根语义，要求 HTTPS `archive_url`，不登记或校验归档与内容树 SHA-256；Git 定义不能混入归档字段。Contract 共用完整来源根匹配、来源解析和 checkout 校验。源码不属于 Bundle，不形成图谱节点；离线缺根时只校验路径形状，根已存在时再检查版本与文件。

文档归档 `mirror` 的转换策略同样由 Registry 声明。当前 `navigation_policy: index_only` 表示 README、发布占位、纯链接目录和接口清单不形成 Concept，来源链接改到最近的有效目录 `index.md`；`omit_section_title_contains` 声明只进入结构化元数据、不在知识正文重复保留的章节标题片段。

`api_operator_display_limit` 是正整数，只限制按需 API 引用建议的展示数量。完整调用证据保存在由 Git 忽略的审计报告中，不限制现有正文链接或图谱边。同步器和 Lint 必须共同消费这些声明，不能各自维护隐藏例外。

Contract 对 API/Guide 的归档镜像识别只采用 `primary` 来源；未声明 `role` 的旧来源保留原有匹配行为。显式标为 `supporting`、`example` 等非主来源的归档引用不把整张蒸馏卡变成镜像：卡片仍遵守普通正文约束，也不从辅助文档推导整卡平台。镜像可以保留原文多个 H1，但无 H1 仍失败。正文、平台和文档回归共同调用这一判定；实际镜像的来源绑定、正文保真和元数据仍由文档归档复验检查，不通过改写来源角色跳过复验。

technology 与 scope 的 ID 不得重叠；每个 route 必须声明允许出现的 domain；`precreate_routes` 只能是布尔值；标签 ID 前缀必须与其维度一致。完整结构由 Contract 在加载时检查。

新增注册值必须同时满足：现有值无法准确表达需求、归属和语义明确、有真实知识或确定性消费者即将使用，并在同一变更补充接受/拒绝测试和检索回归。若属于 `ops` 或 `model`，还要同步其 route 结构入口；其他领域由维护者随真实内容创建路径。不要只为来源别名、任意占位或一次性任务扩充 Registry。

Scope 的公共对象和场景分支形状由 Frontmatter Schema 定义；各 namespace 的适用范围、维度配置、值与别名由 `scope_schemas` 独立定义。`contracts/scope.py` 组织校验与三态匹配，`contracts/scope_matchers.py` 的受控处理器表按维度 `kind` 分派定义校验、值归一化和比较；卡片加载、Ingest、Lint 与构图共用这一路径，不各自定义语法。Contract 提供比较接口，Query 的场景 Scope 参数及过滤接入由其公开消费能力决定。

现有处理器为 `enum` 与 `required_set`。枚举使用独占 `[any]`，必需集合使用非空 `all_of`，并由维度的布尔配置 `query_none_of`、`card_none_of` 分别控制查询与卡片能否声明非空 `none_of`。允许否定的集合可只写 `none_of`，或与 `all_of` 同时声明；正反集合不得相交，缺失成员不表示未启用。当前模型推理的 `parallelism` 对卡片和查询均允许否定，`model_features` 仍只允许查询否定，其他维度不自动获得此权限。这些模型字段和权限不约束其他领域的维度设计。

namespace 至少声明一种非空适用范围：`routes` 绑定合法的 `domain/route`；`domains` 只绑定 Registry 允许直接承载 Profile 的领域及其无 route 路径，例如 Runtime 的直接 Concept 或 Runbook。两者可同时声明，但不会隐式扩展到未列出的 route；Profile 自身仍须允许 `scope`。新增领域应随真实过滤需求登记 namespace 和回归，不为未来领域建立占位 Schema。未注册 schema、处理器类型、非法值或错误路径绑定失败关闭。

领域新增匹配语义时，在当前安装的 Contract 包内增加确定性处理器并登记到受控表，使用 `normalize` 校验及规范化卡片/查询条件，使用 `compare` 返回 `DimensionMatch`。处理器独立检查其配置与值形状，可以使用不同于枚举、集合的条件结构；必须以明确原因报告未知或冲突，不能把缺证据当作匹配。公共聚合仍保持场景内 AND、场景间 OR、任一明确冲突不被未知掩盖，且不跨 namespace 推断。处理器不得联网、执行上游源码或写知识卡；Registry、知识卡、查询参数及外部知识根不能指定 Python 模块、文件路径或执行任意表达式。扩展必须覆盖接受、拒绝、未知、原有语义兼容及实际消费者；修改同版本 Contract 后由维护者重建索引。

Scope 本身始终可选，可只写有来源依据且有过滤价值的部分条件。Lint 不把缺少 Scope 或缺少维度视为质量错误，不以填写率验收；当前 Query 仍使用原有过滤与排序，不能从字段存在推断场景过滤已接入。

集合匹配分别检查卡片要求启用与未启用的成员。查询明确关闭必需成员、或明确启用卡片禁止的成员时为冲突；任何必需状态未确认时为未知。只要任一必要条件明确冲突，就不能用另一项未知掩盖冲突；多个场景仍逐对匹配，不跨分支合并条件。

Registry 或 Contract 更新后，原索引按治理指纹失效，必须由维护者重建；Query 不自行重建。旧 receipt 仍按完整 provenance 校验，不跨治理版本自动放行。回退前先移除依赖新 Schema 的声明，再还原同版本治理文件并重建索引；不得让旧消费者静默忽略无法识别的条件。

## 执行关系

```text
                         frontmatter.schema.json：字段形状
知识路径 + Frontmatter ── profiles.yaml：Profile、OKF type、字段组合
                         registries.yaml：受控路径和值
                                      │
                                      ▼
                            governance Contract
                knowledge.py 门面 + checks 分类实现 + indexes 生成
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
                 Ingest             Query              Lint
                 写前拒绝           加载失败关闭        只读报告
                                      │
                                      ▼
                              本地图谱构建前校验
```

图谱复用同一 Contract 校验知识卡和正文链接，仅以 Concept 为节点、卡片间已有 Markdown 链接为有向 `links_to` 边；API 与算子关联也使用这些链接。Index 不进入图谱，不从目录或语义相似性推断边。构图按需执行，只在 Git 忽略的 `artifacts/graphs/` 写派生产物，不依赖判定缓存或回写知识卡。

## 为什么需要 Contract

JSON Schema 只能检查单个对象的形状，不能独立完成：

- 从路径推导 domain、technology/scope、Profile 和 Bundle 相对 Concept ID；
- 校验卡片 `type` 等于 Profile 的 `okf_type`；
- 判断 route 与 domain 是否允许组合；
- 校验 Operator 和 Runbook 附加层级；
- 要求 `tags` 同时覆盖 task 和 topic；
- 限制 `agnostic` 与具体平台混用；
- 比较 `created_at` 与 `updated_at`；
- 判断来源位于已登记本地根目录或使用 HTTP(S)，并判断识别出的 Git URL 是否固定到 commit；
- 校验 `verified` actor、`replaced_by` 和跨技术端点；
- 校验 Bundle 根版本、必需协作骨架、逐层索引和 Bundle 内 Markdown 链接。

这些规则统一放在 Contract，不通过某个 Skill 的局部例外实现。

## 机器检查与人工审阅

机器规则可以证明结构一致、取值受控和引用目标存在，但不能证明：

- 来源当前可访问且充分支持正文；
- 技术语义、实验和平台边界正确；
- shared 知识足够通用；
- 两种 DSL 的行为真正等价；
- `verified` 事件对应的复核实际发生。

后一类问题必须由贡献者和 reviewer 判断。机器声明、Contract 和 Spec 不一致时，应在同一变更修复事实源、执行逻辑、文档和回归，而不是选择其中一份绕过。

## 修改规则

| 变更 | 至少同步 |
|---|---|
| Frontmatter 字段 | JSON Schema、相关 Profile、Contract 消费、Frontmatter 文档、正反测试 |
| 路径 Profile | Profile、路径深度或特殊规则、路径/Frontmatter 文档、检索回归 |
| domain、technology 或 scope | Registry、路径接受/拒绝测试、Query 过滤、导航 |
| platform、标签或附加路径值 | Registry、真实消费卡、Lint/Query 回归、相关文档 |
| 删除、重命名或收紧规则 | 全部知识卡、evals、受影响的 Skill 和兼容性说明 |

修改后运行仓库统一质量检查。新增规则必须覆盖至少一个接受案例和一个拒绝案例，不能只修改声明让当前样例通过。
