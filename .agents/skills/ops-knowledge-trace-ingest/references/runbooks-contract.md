# Runbooks 落库契约（trace 摄入视角）

把 AscendC 算子开发会话中沉淀的实战知识，按**问题现象/任务**组织成 `knowledge/ops/ascendc/runbooks/<area>/<slug>.md` 下的 OKF Runbook 卡。
本文件是 `ops-knowledge-trace-ingest` skill 的**落库契约参考**，只保留 trace 摄入特有的生产语义；卡片字段、路径、Profile 和词表的机器事实源是：

- 路径与 Runbook 语义 → `governance/specs/paths.md`
- frontmatter 字段 → `governance/specs/frontmatter.md`
- 字段白名单 / 数据类型 / 基础枚举 → `governance/schemas/frontmatter.schema.json`
- domain / route / 平台 / 标签 / runbook area / 受控附加层级 → `governance/schemas/registries.yaml`
- 路径推导、跨字段/文件关系、索引和链接 → `governance/contracts/`

`type` 在入库时由路径 Profile `runbooks` 的 `okf_type`（`Runbook`）决定，卡片不得手工另设 type 值。

## 0. 核心思想

检索端的真实查询形态是"我遇到现象 X / 我要做任务 X，怎么解"。故知识按**现象或任务**组织成 Runbook 卡，检索键 = `title/description/tags + 正文 ## 现象 / ## 适用场景 / ## 验证信号`。
一张卡 = `现象（或任务）× 判别信号 × 处置步骤（切入层）`，附实测验证信号与适用边界。

**卡必须携带证据**：每条结论可回溯到开发过程（正文 `## 验证信号` 用自然语言描述实测：轮次、数值、通过/失败，并逐条标注来源平台与证据等级）。**frontmatter 不设 `evidence` 字段，正文也不要求内部 trace 锚点**（`sha#seq` 类引用只进 `.build/` 中间产物，见 §11）。知识卡是**系统经验**的载体——正文尽可能保留**系统信息（环境/目录/文件清单）与完整代码示例**（before/after 函数级完整代码块，**一律正文内联**，不依赖外部附件文件），让下一个 agent 不只看懂"怎么修"，还能直接复用"完整解法"。

**足量原则**：一张卡是"完整经验单元"而非最小修复笔记。凡 trace 有证据的知识维度（what worked / what failed / root causes / error-fix lessons / reusable strategy / avoid / next attempt / code design）都必须成文、不留空；同时尽可能引入**代码设计知识**（`## 设计决策`）。缺证据的维度宁可标"无证据/未尝试"，也不可省略该维度不写。

**代码信息优先（code-first）**：正文是**代码开发知识**的载体——从 trace 的代码写入事件恢复**每文件的版本时间线**，卡内 before/after 与 `## 完整代码` 必须是**函数级完整代码块、正文内联**（弃用 `okf:attachment` 附件机制）。凡涉及代码改动的卡，`## 判别方法`/`## 解决配方` 必须携带完整 before/after 代码（HARD 约束 17）；完整配方类 Runbook 必须含可执行完整实现（HARD 约束 12）。

**反投机取巧（anti-shortcut）**：放宽容差、修改测试用例/期望值/参考 oracle、删减或跳过失败用例、把失败标注为"已知问题/环境问题"放行、换宽松 metric、固定随机种子绕过统计用例等**"测试侧放松"**做法，即使 trace 中因此"通过"，也**不得作为正知识落库**（只允许作为 `## 坏实践` 负知识）；`## 验证信号` 只收**本 trace 内**实测信号，引用 trace 外记录（"前序 LOG.md 记载、本 trace 未复现"）属 hearsay，不得进验证信号（HARD 约束 16/18）。

**知识价值门槛（宁缺毋滥）**：一张卡必须让**下一个开发者**少走弯路，否则不产卡。候选须同时满足四条价值判据：
1. **垂域绑定**——知识绑定 AscendC/NPU/工具链/评测机制的特有行为，不是任何软件工程通用的常识；
2. **非显然性**——根因或解法是下一个 agent 大概率踩坑或想不到的；
3. **可复用性**——有可迁移的完整配方/代码/检查清单，或至少能改变下一个 agent 的行为；
4. **可验证性**——有本 trace 内 `tool_observed`/`artifact_verified` 信号锚定；对纯流程卡尤其严格。
**明确不产卡**：agent 编排/加载重试/工具定位等通用 LLM 行为；无垂域因果的环境配置问题；无失败-修复闭环的纯流程描述；转写不完整（无 tool_result）无法验证的闭环。**一条 trace 产出 0 张候选是合法结果**，不是挖掘失败。

**适用性与路线（检索前的第一道滤网，必填）**：每张卡必须讲清“这条知识**在哪个场景被真正验证有效**”。正文开段 `## 适用场景` **必填**——工程形态、API 路径、验证过的平台与 CANN 版本、适用粒度（`transfer_scope` 五档取证据能支持的最窄档）、路线优先级（`recommended_fastpath`/`safety_fallback`/`banned` 三档必标其一）、明确不适用/未验证场景。`platforms` **只填实际验证过的平台**（注册词表见 `registries.yaml`）；miner draft 无法定位时可写空表 `[]`，但 curate 必须 defer，不能以 stable 发布。推断可迁移的平台在 `## 失效边界` 标注“未验证，推断可迁移”，不得写进 `platforms`。`safety_fallback` 卡必须明写 fallback 声明。

**统一准入基准（第一道闸）**：每张卡的基准要求都是**完整场景描述**——`## 现象`/`## 适用场景` 用自然语言讲清"**在做什么**（命令/步骤）、**哪个算子哪个文件**、**看到什么报错（原文）**、**当时代码什么状态**"，让人不看 trace 就能理解；**禁止用内部编号（Task N/轮次/会话 id）与"Agent 转述"代替原始输出**；涉及代码的卡必须把**关键代码原样内联**（before/after verbatim 函数级），语言+代码双通道成立才过第一道闸。

## 1. 与 OKF / 本仓治理的关系

| 维度 | 做法 |
|---|---|
| 通用原则 | 遵守 `governance/specs/okf.md`/`paths.md` 的 snake_case、无序号、无嵌图和 index 只列本层；目录表达结构，tags 只表达问题主题与诊断线索 |
| `resource` 溯源 | 按 `governance/specs/frontmatter.md` 来源规则处理；trace 摄入卡 `sources` 可空 `[]`，溯源在正文 `## 验证信号` 段首（§11） |
| `description` | OKF 要求每卡有（index 列条目用），**必填非空** |
| 扩展字段 | Runbook Profile 只使用公共必选字段（`frontmatter.schema.json`）与 Profile 可选字段（`aliases`/`verified`/`replaced_by`）。**不设 `cann_versions`、`evidence`/`confidence`/`transfer_scope`/`quality_score`，也不设 kind/category/phenomenon/signal/solution_layer/source_family/reproduce_count/knowledge_form/keywords**。Runbook 不声明 CANN 版本字段（版本边界若确属结论的一部分，写入正文失效边界）。证据强度由复现判定（内部 ledger/manifest）+ 正文 `## 验证信号` 派生，见 §5 |
| `type` 取值 | 由路径 Profile `runbooks` 决定为 `Runbook`；**不另设 `domain`/`kind`/`category` 字段**。四类挖掘轨（precision/build/perf/guide）是内部提取分类（manifest/ledger 内部 taxonomy），**不落卡 frontmatter**；落盘时按 area 选择 `runbooks/<area>/` 路径（`compilation`/`runtime`/`precision`/`performance`/`validations`） |

## 2. 目录结构

```
knowledge/ops/ascendc/runbooks/
├── index.md                          # 顶层 index：只列已有 area 目录
├── compilation/                      # area ∈ runbook_areas（registries.yaml）
│   ├── index.md
│   └── <slug>.md
├── runtime/
├── precision/
├── performance/
└── validations/
```

- `area` 是受控值（`compilation`/`runtime`/`precision`/`performance`/`validations`），目录按需物化：某 area 首张卡片通过审核时才创建 `<area>/index.md`。禁止用"暂无卡"的空 index 预占目录。
- **文件名** = title 的稳定英文 slug，纯 `snake_case`、无前导序号、无 session 前缀；**无 `id` 字段**——卡片唯一性由 slug 文件名保证。
- **错误码进文件名**：现象有关键编译/运行报错码（如 `561002`/`507035`/`161001`）时，slug 应包含该错误码——错误码是精确检索锚点，按码检索直接命中。
- **撞名兜底**：同 area 内 slug 冲突 → 追加 `__<hash6>`。
- **跨 area/跨树链接**：可在正文中引用 `knowledge/` Bundle 内其他卡片，包括其他 area 和分类树。只在有助于理解结论时添加普通 Markdown 链接，不单独做图谱判定。

## 3. frontmatter schema

```yaml
---
type: "Runbook"                        # 由路径 Profile `runbooks` 决定，不手工另设
title: 输出全0 - 多核 total==0 死循环，加早退
description: 多核切分 total==0 时 kernel 静默空跑致输出全 0；Process 循环加早退。   # 必填非空，供 index
tags: [task.debugging, topic.precision]       # 注册 taxonomy canonical tag（至少 task.* + topic.*）
status: stable                          # draft | stable | deprecated
sources: []                             # trace 摄入卡可空；非空须为可核验来源
created_at: '2026-06-30T00:00:00Z'
updated_at: '2026-06-30T00:00:00Z'
platforms: [950, a2]                    # 必填：只填实际验证过的平台（注册词表）；stable 不得为空
---
```

### 字段表

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | ✅ | 固定 `"Runbook"`（由 Profile 决定） |
| `title` | string | ✅ | 现象/任务 + 处置要点，≤40 字 |
| `description` | string | ✅ | 一句话，非空，供 index 列条目 |
| `tags` | string[] | ✅ | 注册 `task.*`/`topic.*` 等 canonical tag，可带深层级（如 `topic.implementation.api_layer.c_api`） |
| `status` | enum | ✅ | `draft`/`stable`/`deprecated` |
| `sources` | string[]/object[] | ✅ | trace 摄入卡可空 `[]`；非空必须可核验（固定 commit/规范 URL/Registry 本地来源） |
| `created_at` / `updated_at` | UTC iso8601 | ✅ | 秒级 `...Z` 格式 |
| `platforms` | string[] | ✅ | 注册平台词表取值；**只填实际验证过的平台**；仅 draft 无法定位时可写 `[]`，stable/deprecated 不得为空 |
| `aliases` | string[] | — | 可选 |
| `verified` | object/object[] | — | 可选 OKF verification event；单事件为 `{by, at}` mapping，多事件为该 mapping 数组，不得写布尔值 |
| `replaced_by` | string | — | 仅 `deprecated` 卡可设 |

## 4. 受控词表与 area 选择

- `area` 取值来自 `registries.yaml` 的 `runbook_areas`：`compilation` / `runtime` / `precision` / `performance` / `validations`。
- trace 摄入的四类内部提取轨（`precision_card`/`build_card`/`perf_card`/`guide_card`）与 area 的**默认映射**：
  - build（编译/工程）→ `compilation`
  - precision（精度）→ `precision`
  - perf（性能）→ `performance`
  - guide（运行时/工程类完整配方）→ 由 curate 阶段按内容判定归 `compilation` 或 `runtime`（涉及运行机制/工具链诊断归 `runtime`，构建/工程流程归 `compilation`）
- 内部证据 taxonomy（`knowledge_form`：`repair_recipe`/`diagnostic_rule`/`negative_result`/`validated_pattern`）与检索词（`signal` 等）**只进 manifest/ledger 等 `.build/` 中间产物**，用于证据角色与聚类，不写卡 frontmatter。

## 5. 证据强度判定（内部复核，不落 frontmatter）

frontmatter **不设 `confidence`/`reproduce_count` 字段**：证据强度由 **证据等级（evidence level）× 复现判定** 在落库/审查时派生，沿袭 trace 摄入的证据模型：

| 证据等级 | 判定 | 允许用途 |
|----------|------|----------|
| `artifact_verified` | 结果绑定到可重建源码状态 / 不可变产物（commit、快照、附件 hash） | 最强单跑证据 |
| `tool_observed` | 轨迹中有工具调用、命令输出或报错记录（`verify_failed`、编译输出、profiling 数据） | 陈述观测覆盖的范围 |
| `agent_reported` | 只有 assistant/user 消息陈述该结果，无工具输出佐证 | **只作假设/线索，不能当实测信号** |
| `inferred` | 纯静态推断（代码对比等），无上板信号 | 不入主库，只 reject 或转 meta |

| 派生 tier | 判定 | 含义 |
|------|------|------|
| `verified` | **证据等级 `artifact_verified` 或 `tool_observed`** 且跨轨迹复现 ≥2 且正文「## 验证信号」含上板信号 | 结论被实践验证 |
| `single_run` | 证据等级 `artifact_verified`/`tool_observed` 但仅单次实测 | 单跑指示，待跨 trace 复现 |
| `inferred` | 仅 `agent_reported`/`inferred` 证据，或纯静态推断 | **不入主库**，只 reject 或转 meta |

- tier 由审查/curator 判定，**不落 frontmatter**（复现计数存 ledger/manifest）。单次轨迹产出的候选默认只能是 `single_run` / `inferred`。**仅 `agent_reported` 的证据无论复现多少次都不算 verified**。
- **`## 验证信号` 逐信号标证据等级**：正文每条验证信号必须标注 `（来源平台：…；证据等级：artifact_verified / tool_observed）`。`agent_reported`/`inferred` 只能作假设或线索，**不得当实测事实写进 `## 验证信号`**；它们应进 `## 误诊` 并如实标注。

## 6. 正文约束（HARD）

以下规则是 trace 摄入落库契约，由本 skill 的 `scripts/field_notes_lint.py`（runbook 正文校验器）与 `knowledge-lint` 通用 Contract 共同执行：

1. **type↔目录自洽**：`type: "Runbook"` 与 `runbooks/` 路径 Profile 一致；area 属于 `registries.yaml` 的 `runbook_areas`。
2. **文件名合规**：纯 `snake_case` slug、无前导序号、无 session 前缀、非字母数字转 `_`；撞名须已加 `__<hash6>`。
3. **必填字段**：`type`/`title`/`description`/`tags`/`status`/`sources`/`created_at`/`updated_at`/`platforms` 齐全；`sources` 可为空，`platforms` 仅 draft 可为空，stable/deprecated 必须有实际平台范围。`title` 不超过 40 个 Unicode 字符。
4. **正文须含 `## 适用场景`**（统一准入基准——完整场景描述，语言+代码双通道）：正文开段写清工程形态/API 路径/验证过的平台与版本/适用粒度/路线优先级/不适用场景（§8 模板）。lint 对缺失报 **warn（聚合为单条输出，不阻塞退出码；存量卡容忍；新卡由审查门禁按 blocker 拦截）**。
5. **验证信号逐条标注**：`## 验证信号` 每条信号必须标来源平台 + 可用证据等级（`tool_observed`/`artifact_verified`）；缺失即 HARD 违反。
6. **普通跨卡引用**：需要时在正文中添加可解析的 Markdown 链接，不维护专用关系块，也不要求每张卡都有相关链接。
7. **无嵌入图片**：`!\[[^\]]*\]\(` 与 `<img` 双查均无命中。
8. **无静默删除**：常规 ingest/upgrade 中，废弃卡使用通用生命周期字段并填 `replaced_by` 后保留（`replaced_by` 与 `status: deprecated` 联动），不得直接删文件。**全量重建例外**：仅当用户明确授权"清空现有 runbooks 并从完整轨迹重新提取"时，允许在 Git 可恢复基线上整树删除；删除前必须记录旧卡数、当前 commit、原始输入 inventory 及导航/检索索引基线，并在同一重建运行中清理指向已删除卡片的正文链接、更新导航与检索索引并写当日 log。重建不得继承旧卡文本、slug 或复现计数；复现只按本轮 inventory 中不同 source SHA-256 的独立轨迹计数。
9. **跨算子禁止内容（默认生效）**：runbook 卡默认面向跨算子复用，卡内一律不得含源算子常量、checkpoint、shape 列表、**绝对**单跑性能分数（score/latency/speedup 的绝对值）。**相对性能代价允许**：`## 验证信号` / `## 性能影响` 可写同一算子内部两条路线的**相对**对比（如"相对 SIMT 路线约 0.05x"），相对代价必须成对出现（写明参照路线）与来源平台，**不得单独报绝对分数、不得写成通用预期收益**。被标 `safety_fallback` 的路线必须保留该相对代价表述。
10. **环境故障纪律**：根因是环境（device unavailable/quota/网络/评测 harness 故障）的知识不得写成 Runbook 卡；无独立 kernel 因果证据时只进 meta。
11. **反投机取巧**：`repair_recipe`/`validated_pattern` 不得以"测试侧放松"为解法——放宽容差、修改 oracle、删减/跳过失败用例或固定随机种子绕过，即使因此"通过"也不得作为正向知识。若轨迹客观证明其危害，可作为明确 `banned` 的 `negative_result`（内部 taxonomy）；否则只作附属坏实践。
12. **机制 artifact 完整**：`repair_recipe` 的代码/配置修复必须为完整因果单元 before/after；`diagnostic_rule` 的 probe/命令与原始观测必须完整；`negative_result` 的尝试实现/配置、客观失败或回退与边界必须可重建；`validated_pattern` 的完整实现与验证必须可直接复用。所有核心 artifact 均正文内联、verbatim，不能恢复时 defer。完整配方类 Runbook 必须含 `## 系统信息` + `## 完整代码`（可执行，正文内联）+ `## 设计决策`。
13. **验证信号禁 hearsay**：`## 验证信号` 只放本 trace 内 `tool_observed`/`artifact_verified` 实测值；"前序 LOG.md/issue 记载、本 trace 未复现"的转述最多进 `## 误诊` 并标注 `agent_reported`。
14. **平台标注**：`platforms` 为**必填**字段，取值必须在注册平台词表内；miner draft 无法定位平台时写空表 `[]`（不伪造值），**空表/缺省不代表通用平台**；curate 遇到空平台必须 defer，不能发布 stable。**`platforms` 只填实际验证过的平台**——推断可迁移的平台不得写入，须在正文 `## 失效边界` 标注“未验证，推断可迁移”；`## 验证信号` 每个数字必须标注来源平台，与 `platforms` 严格一致。
15. **附件机制弃用**：正文**不得出现 `okf:attachment` 引用**；核心 artifact 一律正文内联，无法恢复时按约束⑫ defer。lint 对存量遗留标记报 warn，新落库卡由审查门禁按 blocker 拦截。

## 7. 普通跨卡链接

同根因不同现象、同码不同根因或不同方案的卡片，可以在相关技术叙述中使用普通 Markdown 链接。不在 frontmatter 设 `related` 字段，不维护专用图谱块或固定关系章节，也不要求卡片必须包含链接。

同问题域存在冲突或不同方案时，在正文说明选用条件、适用范围和失败边界，必要时链接对应卡片。Curator 可在 ledger 的 `related_suggestions` 中留下待核对的引用建议，该字段可省略或为空，不要求全库扫描；采用的链接进入 staged card 并随正文一起审查。图谱仅按需从最终链接派生，不增加关系判定门禁。

## 8. 正文规范（蒸馏，非照搬源文）

```markdown
## 现象
<症状特征 + 判别信号的具体值；自然语言还原完整场景>

## 适用场景（必填 — 检索前的第一道滤网）
<本知识在哪个场景被真正验证有效，逐项写清：
- 工程形态：kernel 直调 / aclnn / spec 生成 / 构建 / 评测 …
- API 路径：涉及的 API / 模板 / 工具链入口
- 验证过的平台与 CANN 版本：<平台> + <CANN 版本>（与 frontmatter `platforms` 严格一致）
- 适用粒度（transfer_scope 五档，默认取证据能支持的最窄档）
- 路线优先级（三档必标其一）：recommended_fastpath / safety_fallback / banned
- 明确不适用 / 未验证场景
若属 safety_fallback，必须明写 fallback 声明。>

## 判别方法（或 ## 根因 / ## 解决配方）
<真正根因与判别步骤，区别于 agent 的误诊假设（后者记到 §误诊）；before/after 为函数级完整代码、正文内联>

## 设计决策（有设计取舍即必填；完整配方类必填）
<为何选这套方案、放弃的候选及原因、当前方案属哪档路线>

## 系统信息（可选；完整配方类必填）
<toolchain/SOC/版本、目标平台、目录布局、相关文件清单>

## 完整代码（可选；完整配方类必填）
<完整可复用的 before/after 代码或分步实现，函数级完整代码块、正文内联，verbatim 取自事件流>

## 性能影响（可选；有性能故事时必填）
<相对性能代价，成对出现并标参照路线+来源平台；禁绝对分数>

## 预防
<读用前检查清单>

## 验证信号
<段首先写来源说明（自然语言，不写内部 trace 锚点），再逐条列实测信号：数值 + 来源平台 + 证据等级>

## 失效边界
<什么 shape/dtype/场景下此方案无效；推断可迁移的平台在此标注"未验证，推断可迁移">

## 坏实践
<负知识：对应常见错误做法 + 为何错；被放弃/降级的路线内联为负例>

## 误诊（可选）
<agent 常见错误假设；hearsay 与 agent_reported 转述也落这里并如实标注>

（不设独立 `## 遗留问题` 节——未解决的遗留问题以 **未决项** 条目并入 `## 失效边界`，未追到根因的卡必须把根因深挖列为优先项）

```

### 8.1 证据准入：来源模式 × 内部知识形态

active Runbook 必须有支撑核心技术结论的**最小机制完整证据**。审查先判来源模式（证据从哪里来），再判内部 `knowledge_form`（要证明什么，存 manifest/ledger，不落卡 frontmatter）。

#### A. 固定源码模式（`fixed_source`）

适用于 Issue/PR、上游源码同步，以及任何声称固定版本实现或 API/规范契约的卡。每个机制 artifact 都须标明 40 位 revision、仓库相对 path、symbol/target、行段和精确 blob 链接。

#### B. 轨迹快照模式（`trace_snapshot`）

适用于开发时 worktree 未提交、客观上不存在 base/fixed blob 的本地开发轨迹。它只证明"该开发会话中，这个实现、探针或尝试在记录的平台与步骤下产生了记录的结果"。

1. ledger/review receipt 必须记录**实际读取的归一化轨迹路径**、`raw_source_sha256`、`normalized_trace_sha256`、连续 sequence 与 coverage 校验结果。两个 SHA 属于不同命名空间，不得互相比对并据此拒绝。
2. 每个结论在 `.build/` 的 manifest/reconstruction 中绑定与知识形态匹配的角色锚点；内部 trace id、SHA 和 sequence 不写入正式卡正文。
3. curator/reviewer 必须逐字核对所有机制 artifact，并确认角色锚点落在有效 sequence 范围。
4. 单条轨迹仍封顶 `single_run`；只有至少两条身份自洽、相互独立的轨迹复现同一结论，且每条都满足自身形态的客观信号及 §5 的上板要求，才可升级 `verified`。以 `raw_source_sha256` 去重，同源草稿、目录副本或重复归一化只计一次；合并卡数和聚类 `cross_trace` 不直接作为复现数。确定性校验拒绝 `reproduce_count` 超过已核验不同 raw 来源数，独立性、逐轨迹证据和结论一致性由 reviewer 核实。

内部形态的 trace 角色合同（manifest/ledger 内部）：

| 内部 `knowledge_form` | 必需 evidence roles | 机制完整性 | active 所需客观信号 |
|---|---|---|---|
| `repair_recipe` | `failure`、`before`、`repair_after`、`validation_after` | 代码/配置修复为完整因果单元 before/after | 同轨迹修后 `tool_observed` 或 `artifact_verified` |
| `diagnostic_rule` | `trigger`、`probe`、`observation`、`interpretation` | probe/命令可执行，原始输出完整 | probe 的工具输出；允许没有成功修复 |
| `negative_result` | `attempt`、`observation`、`boundary` | 尝试路线可重建，失败/回退是客观观测 | 同轨迹失败或成对回退信号 |
| `validated_pattern` | `implementation`、`validation` | 完整函数/配置/命令，足以直接复用 | 实现后的编译/运行/精度/性能通过信号 |

## 9. index.md（逐层、只列本层）

- 顶层 `knowledge/ops/ascendc/runbooks/index.md`：只列当前至少有一张卡片的 area 目录 + 各 area 一句话说明。
- area 级 `<area>/index.md`：只列本 area 卡片（用各自 `description`），不深入下层、不跨 area。
- 条目格式由 `governance/contracts/indexes.py` 唯一决定；通过 `python3 .agents/skills/knowledge-ingest/scripts/knowledge_ingest.py --knowledge-root . sync-indexes` 生成，并用同一入口的 `sync-indexes --check` 验证，不在本合同复制格式模板。

## 11. 溯源与迁移边界（正文溯源，frontmatter 不设 evidence）

- **frontmatter 不设 `evidence` 字段**：问题与验证来源用**自然语言**写在正文 `## 验证信号` 段首（哪次开发会话、哪个修复步骤、实测结果如何）；**不写内部 trace 锚点**（`sha#seq` 类只进 `.build/` 中间产物）。
- `## 验证信号` 只收**实测**结果；"前序 LOG.md/issue 文档转述"属 hearsay，不得作为实测信号。
- 不得把 `log/<date>.md` 当作诊断证据。
- **跨算子禁止内容**：源算子 checkpoint、源代码正文常量、任务语义、shape 列表；**绝对** score / latency / speedup 数值（单跑绝对性能只进 `.build/` 中间产物）；只有结论本身就是某 API/平台约束时才允许保留相关 API 选择。**相对性能代价允许**（成对、标参照路线+来源平台）。
- **环境故障**：device unavailable、runtime 服务故障、quota 耗尽、SSH/网络中断、评测 harness 损坏默认属于环境/工作流证据。除非存在独立 kernel 因果证据，否则不得写成 Runbook 卡。
