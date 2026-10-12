# cannbot-knowledge Agent 工作约定

本文件约束在本仓工作的自动化 Agent。它只说明执行规则；仓库介绍见 `README.md`，人工贡献流程见 `CONTRIBUTING.md`，字段和路径的完整语义见 `governance/specs/`。

## 工作边界

- `knowledge/` 是唯一知识正文根，也是唯一 OKF Bundle root。不要在其他目录保存 CANN、DSL、API、算子、调试或优化事实，也不要在知识树内创建嵌套 Bundle。
- `knowledge/` 中除 `index.md` 外的 Markdown 都是 OKF Concept document；Frontmatter `type` 是其 OKF 类型。目录中的 `concepts/`、`apis/`、`runbooks/` 等名称是路径 Profile，两者不能混用。
- `.agents/skills/`、`governance/`、`evals/`、`logs/` 和可重建的 `artifacts/` 是生产、消费与治理设施，`docs/` 与 `recipes/` 是说明和实践文档；它们都不属于 OKF Bundle。
- `docs/` 只解释设计原则和使用方式，`recipes/` 只提供场景化最佳实践。不要在两者中保存 CANN、DSL、API、算子、调试或优化事实，也不要把 Recipe 写成新的强制规则。
- 只修改当前任务需要的文件。开始前检查工作区，保留用户已有修改；不要顺手格式化或重写无关内容。
- 根目录 Shell、`governance/` 与 `evals/` 中的非空 Python/YAML 文件必须保留仓库标准的 CANN 2.0 版权许可头；带 shebang 的文件先写 shebang 再写许可头。根 `LICENSE` 必须保持官方 CANN 2.0 原文，包括原文中的空白；不要用通用格式化器改写。根 `OAT.xml` 是开源扫描策略和 CANN 2.0 matcher 的机器事实源，修改许可范围或模板时同步更新扫描回归。
- 未经用户明确要求，不执行 commit、push、merge、tag、release、发布或修改用户全局环境。
- 未经用户明确要求，不修改 `.gitcode/`；核对 PR 是否涉及该目录时，必须检查相对目标分支的完整差异，不能只看最新提交。CI 命令的兼容适配放在该目录之外。

## 任务范围

- 每个 PR 只修改当前任务明确要求的内容，以及完成该任务不可缺少的导航、日志、规则或测试；不得顺手更新与当前任务无关的知识（尤其例如官方团队维护的 `knowledge/**/apis/**`、`knowledge/**/operators/**` 等内容）。
- 检查失败、官方来源更新或发现存量错误不构成扩大任务范围的授权。对无关问题只记录并反馈，不得为通过检查运行全库同步或批量更新。
- 涉及当前任务之外的知识升级必须另行取得明确授权，并使用独立 PR。
- 对外贡献流程以 `CONTRIBUTING.md` 为准：常规知识建设先提交说明缺口、生产方法和预期效果的 Issue；公共组件新增、优化或主动行为调整先提交说明问题、必要性和方案的 RFC，完成 A/B 实验后提交关联 PR。知识错误、检索脚本 bug 等缺陷修复，以及轻量文档修订，可直接提交 PR，无需前置 Issue/RFC 或完整 A/B，但仍需修复依据、适用的定向验证和质量检查；修复中包含新增能力或主动流程调整时应拆分贡献。所有 PR 均由 committer 检视后合入。Agent 可在当前授权内准备本地改动与评审材料，外部提交、发布仍遵守“工作边界”，不得把尚未执行的实验写成结果。
- 公共组件贡献扩展优先、保持兼容：新增能力优先复用现有扩展点或可选配置，保留默认流程和对外契约，避免复制整套流程。允许缺陷修复和内部重构修改原实现；纠正错误或恢复既定行为适用修复简化路径，主动改变默认流程、接口或既有行为时，RFC 必须说明扩展方式不足的原因、影响、迁移与回退，由 committer 明确检视，并验证原有路径与新增能力。外层评审要求不增加 Skill 的运行权限。

## 维护本文件

- 每次修改仓库定位、目录结构、机器契约、知识生产/消费流程、质量门禁或 Skill 契约后，都要在交付前重新检查本文件。若现有指令已过时，必须在同一变更中同步更新。
- 本文件只保留跨任务、可长期执行的仓库约束。一次性状态、具体 Skill 脚本命令和容易变化的实现细节应分别进入当天日志、对应 `SKILL.md` 或 `references/`，不要在这里堆积。

## 规则从哪里读取

机器规则由下列事实源共同组成，不存在一份可以覆盖其他文件的“最高优先级”规则：

| 规则 | 唯一机器事实源 |
|---|---|
| 字段白名单、数据类型、数组形状和基础枚举 | `governance/schemas/frontmatter.schema.json` |
| 八个公共必选字段、路径 Profile 到 OKF `type` 的映射、Profile 字段组合 | `governance/schemas/profiles.yaml` |
| domain、route、platform、tag、受控附加路径值和文档归档/提交本地来源 | `governance/schemas/registries.yaml` |
| 路径推导、跨字段/文件关系、索引和链接 | `governance/contracts/` |

`governance/specs/` 解释这些规则的语义和边界：修改知识卡重点阅读 `paths.md` 与 `frontmatter.md`；修改机器规则阅读 `schemas.md`；修改 Bundle/OKF 行为阅读 `okf.md`；修改 Skill 阅读 `skills.md`。目标目录的 `index.md` 提供当前内容导航。

Schema、Profile、Registry、Contract、Spec、Skill 或测试若互相矛盾，不要自行选择其中一份绕过。先定位唯一事实源，再在同一变更中修正执行逻辑、文档和回归。

## 修改知识卡

1. 先用 `knowledge-query` 搜索同一主题，阅读候选卡和来源，再明确采用 create、update、merge、split、deprecate 或 defer。不要只因标题不同就新建卡片，也不要自动覆盖已有卡片。
2. 按 `governance/specs/paths.md` 选择 domain、technology/scope 和路径 Profile。算子知识必须区分 DSL；只有真正不依赖单一技术实现的结论才能进入 `shared/`，跨技术映射进入同领域的 `shared/interoperability/`。
3. 按 `governance/specs/frontmatter.md` 填写字段。不要重复写可从路径推导的 domain、route、Profile 或 Concept ID，也不要为单张卡临时增加字段、标签或注册值。
4. `draft` 的 `sources` 可以为空，非 Glossary 的 `platforms` 也可以为空，但这些必选字段不能省略；轨迹沉淀的 `Runbook` 可使用 `sources: []`，但正文必须保留与结论强度相匹配的触发、探针、原始观测和验证信号；其他 `stable` 和 `deprecated` 必须有可核验来源。非 Glossary 还必须有明确平台范围。已知 Git 文件或目录来源必须固定到 40 位 commit；GitCode/GitHub PR 与 Issue 使用其规范工作项 URL；本地来源必须位于 Registry 登记根目录，资源获取脚本必须存在且可执行；Git 本地来源使用 Registry 登记的 root、40 位 revision 和具体路径，恢复后验证远程来源、提交和干净工作区。
5. `status` 表示生命周期，`verified` 表示真实发生的复核事件，两者相互独立。不要因来源固定、Lint 通过或卡片进入 `stable` 而伪造 `verified`；`replaced_by` 只允许出现在 `deprecated` 卡片中，用于指向当前替代 Concept。
6. 正文通常应蒸馏可复用结论，并说明适用条件、失效边界和验证方式；Registry 文档归档中的官方 API/Guide 文档是受控例外：只摄入含独立技术事实的来源页，README、发布占位、纯链接目录和接口清单等导航页不建卡，其链接改指向对应目录的 `index.md`；保留页除 Registry 声明的冗余章节、失效链接目标、Frontmatter 外，完整保留来源正文；可在文末追加普通知识卡链接，或在这些链接之后增加「配套 API 与常见组合」小节。小节内每条链接可以在同一行用「——」附加一句不超过 110 个字符的机制说明；说明只描述两张卡如何配合、适用条件或失效边界，不新增来源正文没有的接口约束，不换行，也不再包含链接或标题。镜像同步只保留这种文末导航。当前“产品支持情况”只用于推导 `platforms`，不重复写入正文。只有主来源 API/Guide 镜像可保留原文多个一级标题，辅助来源引用不获得此例外。其他知识不要大段复制来源，也不要把搜索摘要、聊天记录或模型记忆作为唯一技术证据。正文图片使用带 40 位 commit 和具体文件路径的 HTTPS Git raw URL，不提交本地图片副本或引用分支地址。
7. 新增、删除或移动卡片时同步受影响的每一级 `knowledge/**/index.md` 和正文链接。移动会改变 Concept ID，还必须同步所有 `replaced_by` 引用。
8. 实质知识变更按“日志”一节记录；纯排版和错别字修复不记日志。

## 目录与导航

- 文件名使用小写 `snake_case`，自由主题的集合目录使用复数；Registry 控制的 Operator 源码分类保持其注册 ID。Registry 中注册的所有 domain 根目录必须保留 `index.md`；只有 `ops` 和 `model` 预建注册 route，其他领域的下一层目录随首张真实知识创建。
- Operator 和 Runbook 只能使用 Registry 中声明的附加层级；`concepts`、`apis`、`examples`、`guides` 和 `optimizations` 可增加小写 `snake_case` 主题层级，其他路径 Profile 默认直接放卡片。
- `index.md` 只存在于 `knowledge/`。每个目录都必须有一个索引，完整且无重复地列出直接子目录和直接知识卡，并为每项提供摘要；domain 根和 `ops`/`model` 预建 route 可只有 index，且不表示已有知识覆盖。
- `index.md` 供人阅读：本次新增或修改的一级标题、导航项名称和摘要应以中文表述，API 名、芯片型号、代码符号和报错原文等必要技术标识保留原文。知识卡的 `title`、`description` 会成为索引新增条目的默认文案，新增或修改卡片时应写成中文可读的标题和摘要；确需保留英文原题时，在索引的显示名称和摘要中补足中文说明。
- 只有 `knowledge/index.md` 声明 `okf_version: "0.2"`，其他索引不带 Frontmatter，所有索引均不参与知识检索。
- Concept 间和索引中的本地 Markdown 链接必须解析到 `knowledge/` Bundle 内的现有文件；知识卡可另行链接 Registry 登记的固定提交本地源码，源码链接只用于来源导航。图谱按需从现有卡片链接生成，只包含 Concept 节点和有向 `links_to` 边，API 与算子关联也使用普通链接；Index 和源码不进入图谱。新增或更新知识不要求构图、关系候选、Agent 关系判定或缓存，也不维护专用关系块。图谱 JSON 和可视化只写入 ignored 的 `artifacts/graphs/`，构图不修改知识卡。
- API→Operator 的现有链接作为普通正文保留。需要发现新的引用时，可按需扫描算子卡声明的固定提交源码并输出引用建议；不自动回写知识卡，不因没有建议或未运行扫描阻断入库。源码调用证据仍须区分语法直接调用与运行时可达性；图谱本身只消费最终正文中的链接，不扫描源码。

## 修改治理和文档

- 先修改规则所属的唯一机器事实源，再同步受影响的 Contract、知识卡、Skill、Spec、正反测试和检索回归；不要在某个消费者里增加局部例外。
- 新字段、新注册值和新规则必须有稳定语义、实际消费者以及至少一个接受案例和一个拒绝案例，不能只为当前样例或未来占位而增加。
- 五份治理 Spec 分别负责 OKF、路径、Frontmatter、机器契约和 Skill。内容能并入现有职责时不要新建碎片化 Spec。
- 仓库级文档只描述当前仓库的定位、能力、语义和边界，不记录其他仓库的迁移过程，也不宣称尚未实现的能力。
- 根 `README.md` 直接维护 `docs/` 和 `recipes/` 的文档导航；`index.md` 仍然只用于 `knowledge/`。新增、删除或移动文档时同步根入口。
- Recipe 使用任务式名称，包含适用范围、预期产物、验证方式和失败/停止条件；它可以引用规则和 Skill，但不能复制规则定义或 Skill 内部接口。
- Skill 的脚本、参数和内部运行方式只写在对应 `SKILL.md` 或 `references/`；README、贡献指南和治理 Spec 只说明 Skill 本身及其输入输出边界；历史日志可记录实际执行过的命令，不作为接口说明。
- 实质治理或 Skill 契约变更按“日志”一节记录；纯排版和错别字修复不记日志。

## 修改 Skill

- 当前维护 `knowledge-ingest`、`knowledge-query`、`knowledge-lint` 三项基础 Skill、复用 Query 的只读 Ascend C API 专用消费流程 `ascendc-api-knowledge-query`、知识仓内的 `ops-knowledge-trace-ingest`（trace → runbooks 生产），以及 `ops-knowledge-vv-ingest`、`ops-knowledge-cv-ingest` 两项源码级 Operator producer。新增其他 Skill 仍需证明现有职责无法承载并完成架构评审。
- `.agents/skills/` 是本仓 Skill 的规范源。Skill 的实现、说明、参考资料和测试都在本仓维护与验证。
- 项目安装通过本仓安装器链接到完整 checkout，保持 Skill、相邻依赖和 `governance/contracts/` 同版本可用；配置知识根不等于支持独立复制 Skill 目录。
- 治理、安装、检索与 CI 回归集中于 `evals/`；Ingest 通过全库确定性命令和仓库级回归验证，trace producer 保留其专用脚本回归。按需图谱与 CI 共用 Ingest 的同一链接构图实现。
- 官方文档归档持续更新，不校验归档或内容树 SHA-256；完成标记记录来源 URL 与准备时间，刷新来源不自动更新知识卡。Git 源码继续固定到登记的 40 位 commit。
- 统一安装入口是根目录 `install.sh`。远程执行时默认自动克隆或仅快进更新托管知识仓；更新已有托管仓前必须确认当前分支与请求分支一致，从已有本地知识仓执行时复用当前 checkout，不自动切换或更新当前分支。安装器按 `requirements.txt` 补齐缺失的 Python 运行依赖，随后默认恢复登记的文档归档与固定版本源码，再准备 Query 索引；显式离线模式可以跳过仓库更新和资源获取，且不要求本地 checkout 的 origin 匹配默认远端。Query/Lint 本身不得自动联网。资源只放在 ignored 来源根，不执行上游源码或覆盖有本地修改的 checkout。
- Skill 保存生产、查询和治理知识的工作流、工具及必要的小型参考资料；可被复用的技术事实必须写入 `knowledge/`。Ingest 按需构图只读取现有链接，不回写知识正文。
- `consumer` 和 `contributor` 是安装模式，不是路径 Profile、OKF `type` 或知识分类。
- `ascendc-api-knowledge-query` 与 `knowledge-query` 一起安装，复用同一索引、平台识别和审计契约；API 头文件线索以已确认的 AscendC 包根解析，不能按知识仓根拼接或跨版本猜测。相关链接只帮助按需补齐证据，不要求遍历全部邻接卡片。
- 修改 Skill 时同步更新其 `SKILL.md`、`references/`、确定性实现和测试。规范源保持 Agent 平台中立，不在 Skill 内保存 `agents/openai.yaml` 等单一客户端元数据；客户端适配由本仓安装器在 Skill 外处理。

## 日志

- 实质知识、治理或 Skill 契约变更必须写入当天 `logs/YYYY-MM-DD.md`；日志只记录已经发生的操作和结果，不充当规则事实源或待办列表。
- 写日志前读取系统时钟，例如 `date '+%Y-%m-%d %H:%M'`。文件日期和条目 `[HH:MM]` 必须来自同一次读取，不得凭上下文猜测、使用未来时间或补造时间。
- 当天日志按时间倒序排列，最新条目放在文件顶部；保留已有历史条目，不为整理措辞而改写过去记录。
- 条目使用 `## [HH:MM] <operation> | 标题`、`### Summary` 和 `### Details`。纯排版、空白或错别字修复不记日志。

## 验证与交付

- 日常修改只做与本次变更直接相关的定向检查，不在每轮修改后重复完整测试流程；以下全库门禁集中在提交或推送上库前执行，用户明确要求提前全量验证时除外。
- 上库前，知识变更至少完成全库 Lint，并用一个与目标场景一致的查询验证召回；新增、删除或移动卡片不能只做单卡检查。
- 治理规则变更必须覆盖接受与拒绝行为；Query 行为变更必须覆盖过滤、排序或失败关闭语义。
- Skill 变更必须验证结构、正常路径、错误路径和权限边界。图谱工具变更还须验证普通链接成边、API 与算子关联保留、无链接不推断关系、无缓存可构建、重复运行幂等、无知识卡写入、非法链接拒绝，以及产物只写入 ignored 目录；日常生产不要求构图或校验图谱缓存。
- 提交或推送上库前统一运行 `bash check.sh`；该门禁不主动获取或严格复验滚动官方来源。来源升级由维护团队在对应专项任务中另行获取并复验。普通修改交付说明已做的定向检查和留待上库前执行的完整验证。
- 最终说明实际修改的文件、关键语义变化、运行过的检查及结果；未执行或失败的检查要明确说明原因。
