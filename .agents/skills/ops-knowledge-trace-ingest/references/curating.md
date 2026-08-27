# curate 阶段：候选草稿 → 门控审查落库 + 复现升级

> **curate 阶段细则**——本文件是 [`ops-knowledge-trace-ingest`](../SKILL.md) 的策展落库阶段准则；主流程/阶段切换见 [`SKILL.md`](../SKILL.md)。**执行方式**：本阶段默认由 [`subagents/ops-knowledge-trace-curator.md`](subagents/ops-knowledge-trace-curator.md)（判定，产出 ledger）与 [`subagents/ops-knowledge-trace-reviewer.md`](subagents/ops-knowledge-trace-reviewer.md)（独立审查）subagent 执行，主 agent 按 ledger 单一收口落盘；批量模式按簇级判定（§批量模式）。无 subagent 环境时主 agent 按本文件直接执行（两轨并存）。本文件是两种执行方式的**单一准则权威**。



把 miner 暂存的候选草稿，经**门控 + 独立审查 + 新颖性/去重**就地增量落盘到 `knowledge/ops/ascendc/runbooks/`，或在 `upgrade` 模式下跨 trace 合并去重、升级置信度。本 skill 是挖掘段的**策展落库对偶**：读草稿与 reconstruction（干净上下文，不读 trace 长文）、对齐现有库、落盘。

> **全流程模式下 curate 自动跟随 mine**（SKILL.md §阶段切换）：mine 产出候选后主 agent 不停顿，直接进入本阶段的 ingest 流程；仅当用户显式只要求 mine（如攒批）时，本阶段才由后续指令触发。

设计借鉴：
- 落盘 schema / 目录 / validator → [`references/runbooks-contract.md`](runbooks-contract.md)。
- 独立审查 / ledger 终态 / 统一收口 → 源自 `ops-knowledge-trajectory-ingest` 的生命周期设计。

---

## 核心纪律（违反即废）

1. **就地增量，绝不整体重写**：落盘只做条目级 delta（新建卡 / 合并字段 / 补反链），不重排既有卡（防 ACE context collapse）。
2. **门控先行**：候选过不了门控的不落库，只进 ledger/meta 报告（deferred/rejected）。
3. **独立审查**：落库前用全新 reviewer 上下文审查改动（§独立审查）；reviewer 只能输出 findings，不能编辑卡片。
4. **新颖性/去重**：已覆盖的不重复 ADD——同 nugget 走 UPVOTE（`reproduce_count+1`）或增量合并（补失效边界/坏实践）；新颖的才新建卡。
5. **不静默删除**：常规 ingest/upgrade 中，废弃卡填 `replaced_by` 并保留（**设 `replaced_by` 的废弃卡须同时置 `deprecated: true`（即 `status: deprecated`），保留文件不删**——统一 Contract 对设了生命周期字段而未置 `deprecated` 的卡报 blocker）；改"已验证"旧卡前先回归检查。用户明确授权的 `rebuild` 是唯一例外：按 runbooks-contract 约束先留 inventory/基线，再整树删除并在同轮重建，不逐卡设置生命周期字段。
6. **职责隔离**：只读 miner 草稿 + reconstruction + 现有 runbooks 库，**不读 trace 长文**（防轨迹细节误入知识卡）。
7. **OKF 合规收尾**：纯 slug 文件名、type↔目录自洽、index 只列本层、「## 相关」双向闭合、代码完整为**正文内联**（无 `okf:attachment` 附件引用）、validator HARD=0。
8. **统一收口**：index/反链/代码内联核对/coverage/log 由主 agent 一次性写入（单一 finalizer），不分散零散改。
9. **可追溯**：落盘后写 `logs/<YYYY-MM-DD>.md` 条目（本仓规范）+ meta 报告（`.build/ops-knowledge-trace-ingest/`）+ ledger 终态。

---

## 相关性判定（与 AscendC 算子开发的关系）

runbooks 是**算子开发知识库**：只收"Agent 编写/调试/优化 AscendC 算子时反复踩坑、找到解法"的知识。判定标准：

**PASS（算子开发核心）**——知识绑定 AscendC/NPU 特有行为，违反后**错误不可见（静默错/时好时坏）或需重写设计**：
- API 语义契约：DataCopyPad/DataCopy 参数单位与对齐（blockLen 字节、dstStride pitch、32B 目标对齐、uint64 偏移）、cast 三兄弟（CAST_ROUND/RINT/NONE）适用语义、TQue/TBuf 生命周期、TilingKey/TilingData 传递
- 硬件架构约束：UB 容量与 buffer 复用、bank conflict、搬运粒度、MTE2/MTE3/V 流水与 PipeBarrier 同步可见性
- 运行/编译机制：多核切分与负载均衡、模板分发、数值稳定（bf16 误差链、相消、NaN 传播）、平台差异（950 arch35 vs A2/A3）
- 算子侧实现决策：tiling 策略选择、数据排布、同步最小充分条件

**REJECT（外围，不产卡）**——一次性、查文档即解、不影响计算语义：
- 通用软件工程：环境变量（PYTHONPATH 等）、锁文件/stale 进程、文件权限、CMake 通用配置（不涉算子特有架构语义）
- 工具操作步骤：msprof/dump 具体命令、编译器参数、TTK 工具参数语义
- agent 工作流/治理：门禁绕过、编排重试、工具定位、流程合规
- 评测 harness：wrapper 脚本、计时循环、输出重算、测试数据生成脚本（不涉算子语义）
- 文档/格式：README 对齐、表格格式、文件名截断
- **spec 校验规则类内容**：Sancity 校验器/工具链自身的规则说明、spec schema 校验打回、与算子 kernel 行为无关的 workflow 规则——这种卡"拿走后下个 Agent 只在 spec 阶段被工具打回，不会踩 kernel 坑"，不产卡（判别测试不过）
- **弱相关卡（workflow_only）**：Agent/工具流程建议、不宣称 kernel 行为的内容——即使垂域相关，也只作流程建议，**按 `transfer_scope=workflow_only` 路由出库**（不落 runbooks 主库，进 meta/ledger 报告），不得以"勉强相关"身份落卡

**判别测试**：把这条知识从库里拿走——下个 Agent 写/调算子时还会不会踩同一个坑？
- 会（错误不可见/需重写设计/查文档也想不到）→ PASS
- 不会（跑一遍、查文档、重装即解）→ REJECT

**边界情况**：spec.yaml 算子规格、构建产物（.so 符号、opbuild 行为）若绑定算子特有机制算 PASS；同一主题既有"工具坑"也有"算子机制"时，只保留算子机制部分。

---

## 三种模式

| 模式 | 触发 | 输入 | 产出 |
|------|------|------|------|
| **ingest** | `ingest <草稿目录或manifest>` | 单条/少量 miner 草稿 | 落盘新卡（`single_run`）/ 增量合并 / reject；`reproduce_count=1` |
| **upgrade** | `upgrade` | 扫 `knowledge/ops/ascendc/runbooks/` 全库 | 跨 trace 合并同 nugget → `reproduce_count` 累加 → 升 `verified`；建 「## 相关」反链；废弃卡 `replaced_by` |
| **rebuild** | 用户明确授权清空重建 | 完整原始轨迹 inventory + 空 runbooks 库 | 不继承旧卡；按本轮 source SHA-256 聚类复现并全量重建 index/图谱/检索 |

> **模式边界**：`verified` 门槛 = 上板信号（`tool_observed`/`artifact_verified`）+ `reproduce_count≥2`，复现计数只在**跨 trace** 时才能涨。ingest 单条落盘只能 `single_run`；攒够一批后跑 upgrade 才能真正升级。rebuild 只改变库的初始状态（空库重建），不放松同一证据门槛。

---

## ingest 模式流程

### 1. 读草稿
读 miner 暂存目录（`.build/ops-knowledge-trace-ingest/<日期>/<trace_id>/`）的 `manifest.json` + `reconstruction.json` + 各 `DRAFT-*.md` 草稿卡。每条草稿已是 runbooks-contract schema 合规（frontmatter + 正文：`type: "Runbook"`，标题 ≤40 个 Unicode 字符，必填 `platforms`——可定位填词表取值、无法定位为 `[]`；**frontmatter 不设 `evidence`/`confidence`/`transfer_scope`/`quality_score`/`reproduce_count`/`kind`/`category`/`phenomenon`/`signal`/`solution_layer`/`source_family`/`knowledge_form`/`keywords`**——内部形态 `knowledge_form` 与检索词只进 manifest；验证信号为自然语言实测描述，内部锚点只进 manifest）。

### 2. 门控（多锁适配，逐条过）
| 锁 | 判定 | 不过的处理 |
|----|------|-----------|
| **实测锚定锁** | 候选须有客观信号（实测 Δ / 精度 N/M / 编译通过），即证据等级 `tool_observed`/`artifact_verified` | 仅 `agent_reported`/纯推断 → `inferred`，**不落库**，转 ledger/meta deferred |
| **证据锁** | `## 验证信号` 有可核验的实测描述（自然语言 + 数值：哪次修改/轮次后得到什么结果）；manifest `evidence_anchors` 有 `sequence/event_type/raw_source/raw_record/raw_sha256` 结构化溯源记录（不要求写入卡正文） | 无实测描述或锚点缺失 → 降级 `inferred`，注明 reason |
| **归因锁** | 增益可归到该轮单点改动 | 一轮混多改动 → 只记方向不记具体分值，或降级 |
| **防作弊/复现锁** | STATE 单跑自评封顶 `single_run`；有标准化 `tasks_eval` 正 Δ 才算强信号 | 单跑自评 → 强制 `single_run`，不升 `verified` |
| **防投机取巧锁** | 解决配方为"放宽容差/改测试/改期望/删用例/hw_compat 豁免"等**测试侧放松**且无代码侧实质修复（runbooks-contract HARD 16） | **reject**（reason=`shortcut_solution`），即使 trace 因此"通过"也不落库；只有明确写成坏实践负知识（`workflow_only`）的才放行 |
| **知识价值锁** | 候选须满足四条价值判据：垂域绑定（AscendC/NPU/工具链特有行为）/ 非显然性（下个 agent 大概率踩坑）/ 可复用性（完整配方·代码·清单）/ 可验证性（本 trace 内实测锚定；workflow_only 从严）（runbooks-contract §0） | **reject**（reason=`low_value`/`domain_generic`/`process_only`/`unverifiable`）；agent 编排/工具定位等通用行为、纯流程描述、转写不完整闭环一律不落库 |
| **相关性锁** | 候选必须与 **AscendC 算子开发**实质相关（判定标准见「相关性判定」小节） | **reject**（reason=`non_ascendc`）：通用软件工程坑（环境变量/锁文件/CMake 通用配置/文件权限）、工具操作步骤（msprof/dump/编译器具体操作）、agent 工作流与治理、评测 harness 脚本问题、文档格式问题一律不落库 |
| **形态化机制证据锁** | `repair_recipe` 有完整因果单元 before/after；`diagnostic_rule` 有可执行 probe 与原始观测；`negative_result` 有可重建尝试、客观失败/回退和边界；`validated_pattern` 有完整实现与验证。核心 artifact 均正文内联、逐字可核 | 用单一“修后 AFTER”门槛拒绝非 repair，或机制 artifact 仅为示意片段 → 退回/defer |
| **active 轨迹证据合同锁** | 每个 adopted claim 有实际 normalized 路径、raw/normalized 双 SHA、连续 coverage、与 `knowledge_form` 匹配的角色锚点、逐字机制 artifact、客观信号、双向 claim mapping 和单点归因（runbooks-contract §8.1 / Errorbook） | 缺任一必备项 → `defer/support`；仅缺 remote blob 不得 defer。fixed revision/blob 有则核验并优先，禁止伪造链接 |
| **场景描述锁** | 候选必含**完整场景描述（语言+代码双通道，统一准入基准，runbooks-contract §0）**：`## 现象`/`## 适用场景` 用自然语言讲清"在做什么命令/哪个算子哪个文件/什么报错原文/当时代码状态"，禁内部编号（Task N/轮次）与"Agent 转述"代替原始输出；涉及代码的卡关键代码原样内联（runbooks-contract §0「统一准入基准」） | 缺场景或关键代码 → 退回 miner 补全或 reject（reason=`missing_scenario`） |
| **验证信号锁** | `## 验证信号` 只含本 trace 内实测；"前序 LOG.md/issue 记载、本 trace 未复现"为 hearsay（HARD 18） | 含 hearsay → 从验证信号移除并降级 `inferred`，或 reject |
| **适用场景锁** | 候选必含 `## 适用场景`（工程形态/API 路径/验证过的平台与版本/适用粒度/路线优先级/明确不适用或未验证场景）；`safety_fallback` 卡必含 fallback 声明 | 缺段/缺关键项 → 退回 miner 补全或 reject（reason=`missing_scope`） |
| **路线优先级锁** | 已标三档路线（recommended_fastpath/safety_fallback/banned）；独立 `negative_result` 可用 `banned` 成卡，其他正向形态中的 banned 只作坏实践 | 未标 → 退回补全；非 negative 卡把 banned 当推荐路线 → reject |
| **平台严格锁** | frontmatter `platforms` 只含实际验证平台；推断平台在 `## 失效边界` 已标"未验证，推断可迁移"；`## 验证信号` 数字标来源平台 | platforms 含推断平台 → 退回移入失效边界；验证信号未标平台 → 退回补全 |
| **相对代价锁** | 正文无绝对单跑分数（HARD 14）；相对性能代价成对出现并标参照路线+来源平台 | 绝对分数落正文 → 移除（provenance 只进 manifest）；相对代价孤值 → 退回补参照 |
| **验证信号等级锁** | `## 验证信号` 每条信号标证据等级+来源平台；`agent_reported` 未混入验证信号 | 混入 → 移除并降级 `inferred` 或 reject |
| **回归锁** | 落盘涉及已有"已验证"卡时，先回归检查旧基线仍成立 | 仍成立则不覆盖（条件分支/补充/标 superseded） |

过门控的候选：有上板信号 → `single_run`（ingest 不升 `verified`，留给 upgrade）；无 → reject/deferred。

### 2.5 价值复核（miner skipped 清单对账）
读 manifest 的 `skipped` 清单（reason：`domain_generic`/`no_domain_cause`/`process_only`/`unverifiable`/`shortcut`/`non_ascendc`/`missing_scenario`）：抽查每条 reason 与被剔除闭环是否相符；**漏网低价值草稿**（常识性/纯流程/转写截断）在本阶段直接 reject（reason=`low_value`）；skipped 与 reject 全部进 ledger/meta 报告。

### 3. 新颖性 / 去重（对照现有库）
对每条过门控候选，检索 `knowledge/ops/ascendc/runbooks/` 现有卡（按 `phenomenon` + `signal` 重叠 + 根因语义相似判定同 nugget）：

| 情况 | 处理 |
|------|------|
| **新颖**（无同 nugget 卡） | 新建卡（见 §4 落盘） |
| **同 nugget 已存在**（同 phenomenon+信号+根因） | **不重复 ADD** → UPVOTE：已有卡 `reproduce_count+1`，正文 `## 验证信号` append 本条证据（含证据等级）；ingest 阶段封顶 `single_run`，达 ≥2 留给 upgrade 升 `verified` |
| **同 nugget 但新卡有补充**（新失效边界/坏实践/误诊/设计决策/遗留问题/更完整代码） | **增量合并**进已有卡对应章节（就地 Edit），不新建 |
| **被现有卡覆盖且无补充** | reject，ledger 记 `covered_by: <slug>` |
| **候选是聚合卡（一根因一个根因闭环的卡内含多个独立根因）** | **先拆分再走上述判断**：按 §细粒度把各根因拆成独立卡分别判 nugget/合并/新建；禁止把聚合卡整张落盘 |

> **细粒度对齐**：库内已有聚合卡（一张卡描述多个独立根因）时，落盘新卡前先与 curator 商定拆分（拆出卡 `replaced_by` 语义保留），再逐根因去重。库索引以**根因闭环**为单位，不鼓励"算子主题卡"。

### 4. 落盘（新建卡）
对新颖候选，就地新建到 `knowledge/ops/ascendc/runbooks/<area>/`（area ∈ `compilation`/`runtime`/`precision`/`performance`/`validations`，按草稿内部四轨映射与内容判定）：
- **文件名纯 slug**：从 title 生成英文 snake_case slug，无序号无 session 前缀；撞名加 `__<hash6>`。**无 `id` 字段**——slug 文件名即唯一标识。
- **错误码进文件名（build 卡优先）**：若现象有关键错误码，在不破坏稳定 slug 的前提下嵌入错误码作为精确检索锚点；存量 kebab-case 路径不因格式治理重命名。
- **补 `description`**：确保非空（miner 已填则校验）。
- **`## 相关`（正文末）**：ingest 阶段可空或建已知反链——在正文末加 `<!-- okf:related:start -->` 块 + `## 相关` 章节，用 markdown 文件超链接（同域 `slug.md`、跨域 `../<domain>/slug.md`），例如 `对侧 title` 指向 `对侧 slug.md`（占位）；双向闭合（对侧卡同步加回链）。
- **冲突/方案关系双侧标注（runbooks-contract §7 硬要求）**：同一问题域出现多路线（fallback 与 fast path、被取代方案、冲突主张）时，`## 相关` 必须**双侧**显式标注关系与选用条件——如"与 X 卡冲突：本卡为安全兜底（safety_fallback），X 为性能路线（recommended_fastpath），按场景选用"；只建单侧链接视为冲突未治理。查到库内同问题域路线卡时，在 `related_suggestions` 记 `{a, b, relation}` 供主 agent 双侧补齐。
- **机制 artifact 核对**：按 `knowledge_form` 核对 repair before/after、diagnostic probe/observation、negative attempt/boundary 或 validated implementation/validation；核心代码/配置均正文内联且逐字可核，附件引用一律退回。
- **足量核查**：落盘前对照 runbooks-contract §8 维度表检查——`## 适用场景`、`## 设计决策`、`## 遗留问题` 与形态主章节；`repair_recipe` 核对 before/after 为完整因果单元，其他形态核对自身机制 artifact；guide 卡核对 `## 完整代码` 可执行；`## 验证信号` 核对无 hearsay、每条信号标来源平台+证据等级、`platforms` 只含实际验证平台。
- **复现判定**：沿用草稿 manifest 的内部 `reproduce_count`（默认 1）；**不写卡 frontmatter**，frontmatter 也不设 `confidence`（tier 由复现数 + `## 验证信号` 判定，记 ledger/manifest，见 runbooks-contract §5）。
- **迁移边界**：沿用草稿正文 `## 失效边界`（跨算子禁含常量/分数默认生效，见 runbooks-contract §11）。
- **`platforms`**（必填）：沿用草稿，核对取值属于 本仓平台词表（`registries.yaml`） 注册值（`950`/`a3`/`a2`）且**只含实际验证过的平台**（与 `## 验证信号` 来源平台一致）；推断可迁移平台须在 `## 失效边界` 已标"未验证，推断可迁移"；无法定位平台的卡保持空表 `[]`（未定位平台，不伪造、不补填）。
- **溯源**：frontmatter 不设 `evidence` 字段（runbooks-contract §11）；草稿正文 `## 验证信号` 段首的来源说明沿用，无来源可写时省略；内部锚点在 manifest `evidence_anchors`。
- **`timestamp`**：取系统时钟（`date`），不臆造。
- 正文照搬草稿（已是 §8 合规），仅修正字段。

### 5. 独立审查（落库前必做）
使用**全新 reviewer 上下文**，只提供：改动卡、ledger、manifest、角色锚点对应的定向 evidence slice 与 runbooks-contract §3-§8。先用 `validate_review_receipt.py --subject` 生成绑定 ledger/全部 staged card 字节的 subject；reviewer 只能输出原样带回 subject 的不可变 receipt，不能编辑卡片：

- finding 严重度必须为 `blocker` / `major` / `minor`。
- 出现任一情况阻止发布（blocker）：
  - 结论没有实测信号或验证来源无法用自然语言说明（自动化产卡 `## 验证信号` 无实测描述、manifest 无 `evidence_anchors`）；
  - `agent_reported` 叙述被写成实测事实；
  - **`## 验证信号` 含 hearsay**（"前序 LOG.md/issue 记载、本 trace 未复现"被当实测）；
  - **解决配方是"测试侧放松"捷径**（放宽容差/改测试/改期望/删用例/hw_compat 豁免）且无代码侧实质修复；
  - **低价值/常识性知识被发布**（agent 编排/工具定位等通用行为、无垂域因果的流程描述、验证信号截断的闭环——价值判据不过，runbooks-contract §0）；
  - **机制 artifact 不完整**：repair 缺完整 before/after，diagnostic 缺 probe/observation，negative 缺 attempt/boundary，validated 缺 implementation/validation；
  - 单条轨迹被标 `verified`；
  - 跨算子卡泄漏源算子语义/checkpoint/常量/分数；
  - 环境/工具故障被误判为 kernel 知识；
  - 仍含密钥或个人信息（核对脱敏 `redactions` 计数）；
  - 静默覆盖已有 verified 结论；
  - **聚合卡**（一张卡描述多个独立根因闭环）——reviewer 必须指出并拒绝，要求拆卡重审；
  - **与 AscendC 算子开发无关**（判定标准见「相关性判定」）；
  - **背景缺失/推导跳步/闭环缺失/假设型卡**（无算子名与场景、根因换算无算式、after 未验证冒充已验证、无真实现象只有评审结论）；
  - **适用场景缺失/路线未标**（无 `## 适用场景` 或关键项缺失；`safety_fallback` 卡缺 fallback 声明；路线与 `## 设计决策` 不一致）；
  - **场景描述缺失（语言+代码双通道不成立，统一准入基准，runbooks-contract §0）**（`## 现象` 用内部编号/Agent 转述代替原始报错输出，看不清"在做什么命令/哪个算子哪个文件/什么报错原文/代码什么状态"；涉及代码的卡关键代码未内联）；
  - **platforms 超验证范围**（frontmatter `platforms` 含推断平台，未在 `## 失效边界` 标"未验证，推断可迁移"）；
  - **验证信号未逐条标注**（每条信号缺来源平台或证据等级；`agent_reported` 被当实测事实写进验证信号）；
  - **绝对性能分数落正文**（绝对 score/latency/speedup 落正文即 blocker，provenance 只进 manifest；相对代价未标参照路线/来源平台）；
  - **同问题域冲突未标注**（存在 fallback/fast path/被取代方案并存却未在 `## 相关` 双侧显式标注关系）；
- 根据 findings 修订后生成新 subject 并重新审查，直到 blocker 和 major 清零；最终 receipt 必须通过 `scripts/validate_review_receipt.py`。

### 6. 统一收口（单一 finalizer）
审查通过后，由主 agent 一次性完成所有共享写入：
1. 更新 `knowledge/ops/ascendc/runbooks/<area>/index.md`：新增条目 `* slug.md — description`，其中 `slug.md` 为占位示例，只列本层；顶层 `index.md` 仅当新增首张卡片的域目录时更新。
2. 跑 runbooks-contract §6 的 HARD 约束（文件名合规、「## 相关」双向闭合、必填 platforms、完整配方类 runbook 完整性、代码完整内联、验证信号禁 hearsay 等）。HARD≠0 按提示修正后重跑至 0。
3. 写 ledger 终态 + meta 报告（含 coverage：每条候选处于 published/deferred/rejected/skipped 且有 reason）。
4. 写 `logs/<YYYY-MM-DD>.md` 条目。

---

## upgrade 模式流程（批量升级扫描）

### 1. 全库扫描聚类
扫 `knowledge/ops/ascendc/runbooks/{compilation,runtime,precision,performance,validations}/` 全部卡，按 **同 `phenomenon` + `signal` 重叠 + 根因语义相似** 聚类成 nugget 簇。每簇 = 同一知识的多份独立复现。

### 2. 合并 + 复现计数
每簇选**质量最高 / 最早**的卡为主卡，其余：
- `replaced_by: <主卡slug>`（保留文件，不删；须同时置 `deprecated: true`，见核心纪律 5）；
- 主卡 `reproduce_count += 被合并卡数`；
- 主卡正文 `## 验证信号` append 各被合并卡的证据（R<n> + 信号 + 证据等级 + 来源 trace hash 脱敏）；
- 被合并卡独有的失效边界/坏实践/误诊/更完整代码 → 增量合并进主卡对应章节。

### 3. 升级 verified
主卡 `reproduce_count ≥ 2` 且证据等级 `tool_observed`/`artifact_verified`（`## 验证信号` 含上板信号：编译过/精度 N/M/实测 Δ）→ 判为 `verified` tier（tier 不落 frontmatter，见 §5）。仅 `agent_reported` 证据**不升 verified**。缺上板信号或复现不足的保持 `single_run`。**回归锁**：升级前检查旧基线仍成立，矛盾则作条件分支不覆盖。

### 3.5 存量捷径卡治理
upgrade 扫描时，检出解决配方为"测试侧放松"（放宽容差/改测试/改期望/删用例/hw_compat 豁免）且无代码侧实质修复的存量卡（HARD 16）：
- **不升级**（`reproduce_count` 不累加、不升 `verified`）；
- ledger 记 `flagged: shortcut_solution`，并在 meta 报告列出待治理清单（转坏实践负知识 / superseded / 删除，需用户裁决）；

### 3.6 存量低价值卡治理
upgrade 扫描时，检出不过价值判据的存量卡（agent 编排/工具定位等通用行为、无垂域因果的流程描述、验证信号仅为截断/叙述的闭环）：
- **不升级**；ledger 记 `flagged: low_value`，meta 报告列出待治理清单（删除或转 meta，需用户裁决）；

### 3.7 方案演进与冲突治理（不建平行卡）
upgrade 扫描发现**同一问题域出现更优/替代方案**（新轨迹证明旧卡是 fallback、被否方案或 banned）时：
- **不建平行卡**：新结论优先**增量合并**进旧卡（`## 设计决策` 补"当前方案属哪档路线"、`## 坏实践` 内联被降级路线为负例、`## 适用场景` 修正路线标注、`## 失效边界` 补"未验证，推断可迁移"）；
- **旧卡降置信度（downvote）**：`reproduce_count` 不因被否路线继续累加；ledger 记 `downvote: <slug>` + reason（`replaced_by_fastpath`/`route_downgraded_to_fallback`/`banned`），并在旧卡 `## 相关` 双侧标注"与 X 卡冲突：本卡为安全兜底，X 为性能路线，按场景选用"；
- **upgrade 不静默改"已验证"结论**：涉及旧卡降级时先回归检查旧基线认知来源，与 `knowledge-routing` 的"复现时更新置信度、不建重复卡"一致；`replaced_by` 仅在新方案完整覆盖旧卡且旧卡无独立价值时使用（同时置 `deprecated: true`，见核心纪律 5）。

### 4. 建「## 相关」反链
跨簇扫描同根因不同现象（如 precision `output_all_zero` ↔ perf `bandwidth_unsaturated`，都源于多核切分）、同现象不同 `solution_layer` 的卡 → 双向 markdown 超链接反链（在「## 相关」章节加 markdown 文件超链接（目标 `slug.md` 为占位），两侧同步加，validator 校验闭合）。guide 卡与其"修复的现象卡"是典型反链对（模板 ↔ 修的问题）。

### 5. index + validator + log
被合并卡 `replaced_by` 后，其域 `index.md` 标注或移至归档（保留文件但 index 不列，或列带 replaced 标）；跑 validator HARD=0；写 log + meta。

---

## 输出

1. `knowledge/ops/ascendc/runbooks/<area>/*.md`：新建卡 / 增量合并 / 升级 verified / superseded 标记（完整代码一律正文内联，无 `.attachments/` 外置）。
2. 各级 `index.md`：只列本层、条目带 description。
3. **ledger + coverage**：每条候选终态（published/deferred/rejected/skipped）+ reason。
4. **log 条目**：`logs/<YYYY-MM-DD>.md` 顶部插入一条 `curate`（`### Summary` + `### Details`——每候选一行放 Details（`操作 锚点 — 信号 — tier(single_run/verified) — 状态(applied/merged/upgraded/superseded/rejected)`），按本仓 `log/README.md` 倒序规则）。
5. **meta 报告**：`.build/ops-knowledge-trace-ingest/<YYYY-MM-DD>-<mode>.md`（gitignored，含变更表 + deferred/rejected 原因 + 审查 findings + 升级明细）。

---

## 与本仓规范衔接

- **runbooks-contract**：本 skill 的落盘契约（§2 目录 / §3 frontmatter / §5 证据 tier / §6 validator / §7「## 相关」 / §9 index / §11 迁移边界与溯源；溯源为自然语言，见 §8 `## 验证信号` 段首）。
- **本仓 OKF 通用原则（`governance/specs/okf.md`） OKF 通用原则**：扁平 ≤3 层、snake_case 无序号、无嵌图、tags 表达层次——全量遵守（`resource` 溯源可选，见 [`references/runbooks-contract.md`](runbooks-contract.md) §1）。
- **log 规范**：本仓 `log/README.md`——事后写、只增不改历史、插入当天文件顶部（最新在前）、时间戳取 `date` 不臆造。
- **git 协作**：本仓主分支 `okf`，改动前 `git pull --no-rebase origin okf`；内容 + log 条目一起 commit，message `curate(runbooks): <mode> <操作摘要>`。
- **图谱（落盘后必做，非条件式）**：落盘后必做图谱增量——图谱工具**不属于本 skill**，位于 knowledge-ingest（`.agents/skills/knowledge-ingest/scripts/build_graph.py`）的 `scripts/` 下：先跑 `python3 .agents/skills/knowledge-ingest/scripts/build_graph.py --knowledge-root .`（全库重建，含新落库卡与跨树邻居）→ 独立 Agent judge 新卡 → 校验 `## 相关` 与判定缓存一致。**runbooks 与 knowledge 其他树的跨树链接由图谱 pipeline 产生，不手写**（手写反链与重建幂等冲突）；删卡/废弃卡同步清理图谱判定缓存。

- **不碰 `reference/` / `ops/`**（本 skill 只管 `knowledge/ops/ascendc/runbooks/`）。

---

## 验证（离线单测）

1. **ingest schema 合规**：落盘卡跑 runbooks-contract validator HARD=0（含必填 platforms、guide 卡完整性、代码完整、反投机取巧、验证信号禁 hearsay）。
2. **门控有效**：无上板信号/仅 `agent_reported`/不过价值判据（常识性·纯流程·截断闭环）的候选被 reject/deferred，不落库；单跑自评封顶 `single_run`。
3. **去重有效**：同 nugget 第二次落盘 → UPVOTE（`reproduce_count+1`），不重复新建。
4. **upgrade 升级**：同 nugget ≥2 份且有上板信号 → 主卡升 `verified`，被合并卡 `replaced_by` 保留。
5. **反链闭合**：「## 相关」双向，validator 校验无悬空。
6. **审查有效**：无实测信号 / 跨算子泄漏 / 环境误判为 kernel / **测试侧放松当正解** / **hearsay 进验证信号** / **before-after 仅示意** 的候选被 blocker 拦下。
7. **无泄露**：落盘卡文件名/frontmatter/正文均无 session_id 与内部结构化锚点（source/raw record/sequence 只进 manifest）。
8. **无整体重写**：`git diff --stat` 行数 sane，单条目级。
9. **log + meta + ledger 齐全**：每次 curate 有 log 条目 + meta 报告 + 候选终态覆盖。
10. **存量捷径卡治理**：upgrade 扫出捷径卡不升级，ledger 有 `flagged: shortcut_solution` 记录。