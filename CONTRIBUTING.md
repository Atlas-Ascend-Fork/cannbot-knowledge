# cannbot-knowledge 贡献指南

本文只说明贡献流程和交付要求。字段、路径与受控值的完整定义由 `governance/` 维护，Skill 的内部命令与参数由各 Skill 自身文档维护，避免在多处复制同一规则。

## 1. 规则从哪里读取

| 需要确认的内容 | 事实源 |
|---|---|
| 字段类型和顶层白名单 | `governance/schemas/frontmatter.schema.json` |
| 各路径 Profile 的 OKF `type` 和字段组合 | `governance/schemas/profiles.yaml` |
| domain、technology/scope、platform、tag 和路径分类 | `governance/schemas/registries.yaml` |
| 跨字段、跨文件和路径校验 | `governance/contracts/` |
| 规则语义和贡献边界 | `governance/specs/` |
| OKF 设计来源和兼容边界 | `governance/specs/okf.md` |
| Skill 触发、流程和内部执行接口 | `.agents/skills/<skill>/` |

Schema、Profile、Registry 和 Contract 共同构成机器规则，Spec 是解释层。两层不一致时，应先在同一变更中修正规则、消费者和测试，再继续写卡；不得通过单个 Skill 的临时例外绕过契约。

## 2. 通用原则

- **可追溯**：技术结论能回到官方文档、固定提交源码、测试或可复核实验。
- **经过蒸馏**：知识卡表达可复用结论，不复制大段文档、源码、Issue 或日志。
- **范围明确**：正文和 Frontmatter 共同说明技术栈、平台、版本、验证范围和失效边界。
- **DSL 隔离**：一个 DSL 的接口、编译器行为和实验结果不能直接写成另一个 DSL 的事实。
- **最小变更**：只修改相关知识、导航、规则、Skill 和测试。
- **可复现**：提供实际完成的查询、校验、测试或最小实验结果。
- **安全**：不得提交密钥、Token、账号、内网地址、私有路径或不可公开数据。
- **不自动发布**：仓库脚本和 Skill 不得自动 commit、push、合并或发布。

集合型目录使用复数，例如 `references/`、`scripts/`、`schemas/`、`specs/`、`evals/`、`artifacts/` 和 `logs/`。

## 3. 贡献知识

### 3.1 先决定如何处理现有知识

写卡前先使用 `knowledge-query` 搜索同一主题，并明确本次决定：

- `create`：没有同主题卡，新增一张；
- `update`：原卡职责不变，补充或修正内容；
- `merge`：多张卡职责重叠，合并为一个稳定入口；
- `split`：一张卡混合多个独立职责，拆分后分别维护；
- `deprecate`：结论仍可解释历史行为，但不再推荐；
- `defer`：来源、范围或验证仍不足，暂不落库。

已确认错误的结论也使用 `deprecated`，并在正文和当天日志明确说明撤回原因；Git 历史保留原结论和更改过程。

不要仅因标题不同就创建新卡，也不要用自动覆盖替代对原卡的完整审阅。

### 3.2 选择路径

知识正文只能进入 `knowledge/`。常规路径为：

```text
knowledge/<domain>/<technology-or-scope>/<profile>/<slug>.md
```

部分 domain 允许直辖 Profile；内容型 Profile 可以增加主题 section，Operator 和 Runbook 则使用受控附加层级。完整 domain-route 矩阵、Profile 说明和合法示例见[知识路径](governance/specs/paths.md)。

选择路径时遵守：

- 目录表达知识适用于哪里，不按来源网站或生产批次分类；
- `slug` 使用稳定的小写 `snake_case`；
- 五个 domain 根目录由 Contract 统一维护；只有 `ops` 和 `model` 预建注册 route。其他下一层路径随首张真实知识创建，不要提前铺设空 route/Profile；
- `operators/` 使用受控 family/category；
- `runbooks/` 使用受控问题域；
- `concepts/`、`apis/`、`examples/`、`guides/` 和 `optimizations/` 的主题 section 使用小写 `snake_case`，并逐层维护索引；
- 稳定原理进入 `concepts/`，接口事实进入 `apis/`，任务型教程进入 `guides/`，完整算子进入 `operators/`，性能方法进入 `optimizations/`，处置流程进入 `runbooks/`。

### 3.3 区分 shared、技术专属和 interoperability

技术专属目录保存依赖该 DSL、框架、编译器或 API 的知识。只有不依赖单一技术实现、且能明确说明复用条件的结论才能进入同领域 `shared/`。

两种技术之间的对应关系进入 `shared/interoperability/`，必须说明：

- 来源技术与目标技术；
- 可以保留的设计意图；
- 必须重新推导或验证的部分；
- 目标技术上的验证证据和当前信任层级。

其他技术栈中的成功经验只能作为线索，不能自动成为目标技术的已验证证据。

### 3.4 准备来源

每张卡都必须填写 `sources`。轨迹沉淀的 `Runbook` 可以使用 `sources: []`，但正文必须保留与结论强度相匹配的触发、探针、原始观测和验证信号，且不能把中间整理仓或会话轨迹伪装成权威 resource；其它非 `draft` 卡至少有一个精确 `resource`。Git 来源固定到提交，文档来源优先使用稳定版本页。仓库相对来源必须位于 Registry 登记的本地来源根目录，并由固定 URL 与归档校验和的获取流程恢复；不能指向未登记根目录、工作区外部或包含路径穿越。性能、精度、平台限制、默认行为和经验性结论必须有与结论强度相匹配的证据。

搜索摘要、PR 标题、聊天记录或模型记忆不能单独作为技术来源。来源角色、固定格式和人工审阅要求见 [Frontmatter 与证据](governance/specs/frontmatter.md)。

### 3.5 填写 Frontmatter

所有非 `index.md` 卡片统一包含八个公共必选字段：

- `type`
- `title`
- `description`
- `tags`
- `status`
- `sources`
- `created_at`
- `updated_at`

额外字段由路径 Profile 决定。`type` 必须写入，但其值由 Profile 的 `okf_type` 唯一决定；不要在卡片中自行创造类型，也不要重复填写可从路径推导的 domain、technology/scope 或 Concept ID。

具体字段语义、生命周期、平台表示、OKF `verified` 事件、信任层级、标签和各 Profile 允许字段见 [Frontmatter 与证据](governance/specs/frontmatter.md)。

### 3.6 编写正文

知识卡应让读者不依赖来源原文也能判断“结论是什么、何时适用、何时失效”。正文通常需要覆盖：

1. 核心结论或适用场景；
2. 必要的机制、参数或操作步骤；
3. 平台、版本、shape、dtype、内存或 workload 边界；
4. 验证方式及证据强度；
5. 与其他卡片的显式相对链接。

不要求所有卡片使用同一模板：概念卡应突出定义和边界，API 卡应突出语义和约束，Runbook 应突出信号、判断和处置步骤，优化卡应突出触发条件、收益来源和失效边界。

### 3.7 更新导航与记录

- `index.md` 只用于 `knowledge/`，且只列所在目录的直接子项；bundle 根索引声明 `okf_version: "0.2"`；
- 新增、删除或移动卡片时，同步受影响的每一级 `index.md`；
- 卡片移动时在同一变更中更新正文链接；本地链接必须留在 `knowledge/` Bundle 内；
- 实质知识或治理变更记录到当天 `logs/`，纯排版和错别字修复不记录；
- 图谱从 Concept/Index、目录层级、人工正文链接和通过指纹校验的多 Agent 关系判定状态本地构建；候选、review、裁决、判定缓存、完整图谱和可视化都保存在 ignored 的 `artifacts/graphs/`，不签入 Git。由判定缓存派生的 `cannbot:related` 受管导航块应同步到知识卡并提交，Query 会将其排除在检索语料之外。

### 3.8 知识提交检查

- [ ] 已明确 create/update/merge/split/deprecate/defer 决定。
- [ ] 路径符合 domain-route、Profile 和附加层级规则。
- [ ] shared 或 interoperability 的复用边界清楚。
- [ ] 八个公共字段齐全，`type` 与路径 Profile 一致。
- [ ] tags 来自注册表，并至少包含 task 和 topic 维度。
- [ ] sources 能定位到支持正文结论的证据。
- [ ] 平台和版本没有超出证据范围；`verified` 如存在，actor 与时间真实可核验。
- [ ] 正文说明结论、适用条件和失效边界。
- [ ] `index.md`、Bundle 内相对链接和当天日志已按需更新。
- [ ] `knowledge-lint` 通过，目标查询能够召回新知识。
- [ ] `bash check.sh` 通过。

## 4. 贡献治理和文档

治理变更必须从唯一事实源开始，并同步所有消费者：

| 变更 | 至少同步 |
|---|---|
| Frontmatter 字段 | JSON Schema、Profile、Contract、Spec、测试 |
| domain/technology/scope/platform/tag | Registry、路径或字段测试、Query 回归、Schema 文档 |
| 路径 Profile 或层级 | Profile、Registry/Contract、路径文档、样板卡、导航 |
| Query/Ingest/Lint 行为 | 对应 Skill、Skill 文档、测试和平台中立的触发契约 |
| 安装契约 | 本仓安装器、Skill 文档和用户文档 |
| OKF 对应关系 | OKF、Frontmatter、Path 文档和 conformance 回归 |

仓库级文档描述能力、输入输出语义和边界；Skill 内部脚本、命令和参数只在对应 `SKILL.md` 或 `references/` 中说明。修改文档时检查所有本地链接，并确认示例描述的是已实现行为。

## 5. 贡献 Skill

当前维护 `knowledge-ingest`、`knowledge-query`、`knowledge-lint` 三项基础 Skill，以及 `ops-knowledge-vv-ingest`、`ops-knowledge-cv-ingest` 两项源码级 Operator producer。VV 用于全部可达 Device 节点均不含 Cube/AIC 或 MIX_CV 的算子，CV 用于至少存在一个可达 Cube/AIC 或 MIX_CV 节点的算子；两者都由任务决定 ACLNN、Host/Tiling 或 Direct Invoke 入口。新增其他 Skill 需要先证明现有职责无法合理承载，并完成架构和发布评审。

本仓 Skill 的规范源位于 `.agents/skills/`，其中维护完整的 `SKILL.md`、`references/`、`scripts/`、测试及其他运行所需资源。规范源不包含 `agents/openai.yaml` 等单一客户端元数据。

Skill 贡献流程：

1. 修改知识仓中的规范源；
2. 更新该 Skill 的内部说明、Frontmatter 触发描述和测试；
3. 验证触发条件、正常路径、错误路径和权限边界；
4. 运行仓库统一质量门禁。

Skill 中只保存完成工作所需的流程、工具和小型参考资料。可被多个 Skill 消费的 CANN、DSL、API、算子、调试和优化知识必须进入 `knowledge/`。

## 6. PR 说明

每个 PR 至少说明：

- 贡献类型和影响范围；
- 知识来源与验证证据；
- 新增、更新、合并、拆分、废弃或延后的决定；
- 实际完成的检查和结果；
- 对检索、Schema、链接/图谱、安装或兼容性的影响；
- 需要 reviewer 重点判断的风险。

## 7. 不接受的贡献

- 无可靠来源的 API、平台、精度、性能或默认行为结论；
- 大段复制上游文档、源码、日志或其他 Skill references；
- 只适用于个人环境且无法复现或界定范围的经验；
- 把单一技术实现过度泛化为 shared；
- 把一个 DSL 的行为写成另一个 DSL 的事实；
- 静默删除仍需要解释的错误或过时知识；
- 自动提交、推送、发布或修改用户全局环境的行为。
