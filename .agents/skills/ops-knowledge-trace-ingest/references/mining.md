# mine 阶段：从归一化 trace 挖掘证据驱动知识候选

> **mine 阶段细则**——本文件是 [`ops-knowledge-trace-ingest`](../SKILL.md) 的挖掘阶段准则；主流程/阶段切换见 [`SKILL.md`](../SKILL.md)。**执行方式**：本阶段默认由 [`subagents/ops-knowledge-trace-miner.md`](subagents/ops-knowledge-trace-miner.md) subagent 执行（主 agent 编排；批量模式每 trace 一个并发）；无 subagent 环境时主 agent 按本文件直接执行（两轨并存）。本文件是两种执行方式的**单一准则权威**。



把一条**已规范化的算子开发会话轨迹**先重建为 `reconstruction.json`（事实/假设/未知），再按**问题现象**蒸馏成若干 runbook 候选草稿，交 [`curate 阶段`](curating.md) 门控落库。本 skill 是冷启动/批量策展的**挖掘段**：只管从 trace 提取，不对齐库、不落盘。

设计借鉴：
- 输出 schema → [`references/runbooks-contract.md`](runbooks-contract.md)。
- 证据等级 / 迁移范围 / 重建纪律 → 源自 `ops-knowledge-trajectory-ingest` 的 evidence-policy。

---

## 核心纪律（违反即废）

0. **细粒度（一卡一根因一形态，宁多勿并）**：每条候选只证明一个独立结论，并标 `knowledge_form`。修复、诊断、失败路线、已验证模式分别满足各自合同；禁止把多个根因或不同形态混成“合集”。
1. **严格按 schema 输出**：每条新候选草稿 = `runbooks-contract.md` §3 frontmatter + §8 正文，字段齐全（`type: "Runbook"`，`title` ≤40 个 Unicode 字符，`status: draft`，trace 摄入 `sources: []`，必填 `platforms`——trace 可定位平台时填词表取值，无法定位写 `[]`；**frontmatter 不设 `evidence`/`confidence`/`transfer_scope`/`quality_score`/`reproduce_count`/`kind`/`category`/`phenomenon`/`signal`/`solution_layer`/`source_family`/`knowledge_form`/`keywords`**——内部形态 `knowledge_form` 与检索词 `signal`/`phenomenon`/`solution_layer` 只进 manifest，不写卡 frontmatter）；溯源写入正文 `## 验证信号` 段首。
2. **仅产候选，不落库**：绝不写 `knowledge/ops/ascendc/runbooks/`，只写暂存草稿（落 `.build/ops-knowledge-trace-ingest/`，gitignored）。
3. **不对齐现有库**：不做去重、不查新颖性、不建 「## 相关」反链——这是 curator 的事。
4. **不升级 verified**：frontmatter 不设 `confidence`/`reproduce_count`；单条 trace 默认 `single_run`。`verified` tier（跨轨迹复现 ≥2 + 证据等级 `tool_observed`/`artifact_verified` + 正文 `## 验证信号` 含上板实测）由 curator 门控判定并记录于 ledger/manifest，见 runbooks-contract §5。
5. **职责隔离**：门禁子 agent 与主 agent 各司其职，门禁只做相关性判定（§相关性预检），不参与挖掘。
6. **证据等级如实判定**：区分 `tool_observed`（工具调用/命令输出/报错记录）与 `agent_reported`（只有 agent 消息声称）。**仅 `agent_reported` 的结论不得写进「## 验证信号」**；每条候选在 manifest 的 `evidence_anchors` 记录内部结构化溯源锚点（`sequence/event_type/raw_source/raw_record/raw_sha256`，不写卡正文，见 §字段映射）。
7. **不堆轨迹原文**：正文叙述应蒸馏，核心机制 artifact 必须完整且 verbatim。`repair_recipe` 的代码/配置修复保留完整因果单元 before/after；其他形态按 runbooks-contract §8.1 保留实现、探针、命令或输出，不附无关外层代码。
8. **足量提取（宁全勿缺）**：每条候选按 runbooks-contract §8 的**知识维度映射表**逐项对照——what worked（解决配方+验证信号）/ what failed（坏实践+before）/ root causes（根因）/ error-fix lessons（预防+误诊）/ reusable strategy（变量化配方）/ avoid（坏实践）/ next attempt（遗留问题）/ code design（设计决策）/ code（完整代码）——**有证据必写、缺证据标"无证据/未尝试"，不得静默留空**；trace 中出现的代码设计讨论（agent 为什么选某 tiling/buffer/API/template、备选方案、被放弃的设计）必须提取进 `## 设计决策`。
9. **不臆造**：缺失的任务/环境/源码/评测信息记入 reconstruction 的 unknowns，不猜测补全。
10. **机制证据优先**：代码写入事件、命令、工具输出和 probe 都可成为知识主源。先为相关文件建版本时间线，再按 `knowledge_form` 恢复最小完整机制单元；核心代码正文内联、verbatim，禁止 1–3 行示意或凭叙述重写。
11. **反投机取巧**：测试侧放松不得作为 `repair_recipe`/`validated_pattern`。若轨迹客观证明其掩盖错误或造成回归，可产明确 `banned` 的 `negative_result`；否则只进坏实践/误诊或 reject。
12. **知识价值门槛**：候选须垂域绑定、非显然、可复用、可验证；可复用性包括配方、诊断规则、失败边界和已验证模式。没有成功修复不再是通用拒绝理由；没有客观观测或机制证据才是。
13. **0 张候选是合法结果**：启动片段、纯问答、无 kernel 联调事件的 trace 默认产出 0 张——"没挖到"不是纪律违规，硬挤低价值卡才是。细粒度数量预期（§细粒度判定）只适用于含完整开发闭环的 trace。
14. **相关性预检先行（relevance gate，mine 入口必做）**：进 reconstruction 与逐事件扫描前，先派 **门禁子 agent**（[`subagents/ops-knowledge-trace-relevance-gate.md`](subagents/ops-knowledge-trace-relevance-gate.md)）——它熟悉 cannbot-skills 的三种 AscendC 算子开发流程（ops-registry-invoke 算子仓开发 / ops-direct-invoke Kernel 直调 / ops-direct-invoke-flash 核函数构建），**只读 trace 开头几轮对话**（~60 事件），语义判断该会话是否涉及算子生成。`unrelated`（与算子生成无关：纯问答/闲聊/他领域任务）→ **立即退出**，不派子 agent、不产草稿，只写最小化退出产物（§相关性预检）；`related`（含"意图明确但仅启动"的会话）→ 继续，价值预筛在扫描中兜底 0 张。**目标是零浪费：无关 trace 的 mine 成本 = 一次门禁调用 + 退出产物。**
15. **场景还原（不抽象、不精简，占篇幅没关系）**：`## 现象` 必须**还原问题发生的完整场景**——用自然语言把"在做什么操作（命令/步骤）、在哪个算子的哪个文件、看到什么报错、当时代码处于什么状态"原样讲清楚，像讲故事一样，不是字段清单；**禁止用 `Task N` / `R 轮次` / `会话 id` / `trace_id` 这类只在当前 trace 有意义的内部编号代替背景描述**（外部读者不知道"Task 19"指什么），换成"在编写 X 算子的 tiling 实现时 / 运行 build.sh 时"这类自然场景；原始命令、报错文本、文件路径、参数尽量原样保留（仅脱敏密钥/个人信息），适当删减无关细节即可。**目标是：没参与过这次开发的人或 Agent 一读现象就知道"当时发生了什么、看到什么报错"**，而不是还要去猜内部编号指什么。
16. **机制推导点破（不跳步）**：`## 根因` 与 `## 解决配方` 中涉及换算/推导/误差累积的关键步骤必须写出**具体算式或机制链**（例：`log1p(y)=ln(1+y)` 要写明；"误差按链步数累积"要给出 `3 步 × epsilon(3.9e-3) ≈ 1.2e-2` 的演算）；禁止用"大约/显然/可推知"带过关键换算；标题口径（如"按 2×epsilon 放宽"）与正文数值必须自洽。
17. **形态合同**：`repair_recipe` 展示完整实际 before/after 与同轨迹修后信号；`diagnostic_rule` 展示触发/可执行探针/原始观测/解释；`negative_result` 展示尝试/客观失败或回退/边界；`validated_pattern` 展示完整实现单元/验证。旧式 `no_validated_after`、`incomplete_code_chain`、`failed_validation` 在 skip 前必须先做形态重分类。
18. **禁止假设型卡**：无真实错误/日志/数值现象支撑的"设计评审结论/预防性建议/若按此实现会怎样"**不产卡**（问题必须真实发生过并闭环）；评审与预防素材最多作为更新既有卡 `## 预防` 的输入，不独立成卡。
19. **适用场景必填（第一道滤网）**：每张草稿必须含 `## 适用场景`（正文开段，`## 现象` 之后）——逐项写清：**工程形态**（kernel 直调/aclnn/spec/构建/评测）、**API 路径**（涉及的 API/模板/工具链入口）、**验证过的平台与 CANN 版本**（与 frontmatter `platforms` 严格一致）、**适用粒度**（`transfer_scope` 五档取最窄：`exact_task`/`same_operator`/`operator_family`/`platform_wide`/`workflow_only`）、**路线优先级**（三档选一）、**明确不适用/未验证场景**。缺场景信息时先回 trace 查证，查不到就如实写"未验证场景：X"并降证据等级，**不得留空**。
20. **路线优先级三档必标**：候选判 `recommended_fastpath`/`safety_fallback`/`banned`。`negative_result` 可以独立以 `banned` 成卡，必须明确失败/回退且不暗示已有修复。`safety_fallback` 若被推荐采用，必须给出成对相对成本。
21. **platforms 只填实际验证过的平台**：frontmatter `platforms` 只写 trace 内**有实测证据**的平台（上板/编译可运行该平台）；推断可迁移的平台**不得写入 `platforms`**，写在正文 `## 失效边界` 并标注"未验证，推断可迁移"。`## 验证信号` 每个数字必须标注来源平台，与 `platforms` 严格一致（同平台才可并入同一结论）。
22. **允许相对性能代价，禁绝对分数**：`## 验证信号` / `## 性能影响` 可写同一算子内部两条路线的**成对相对对比**（如"相对 SIMT 路线约 0.05x"），帮助判断"采用后性能会多差"；**禁止单独报绝对 score/latency/speedup、禁止写成通用预期收益**（HARD 约束 14 明细）。相对代价必须写明参照路线与来源平台；`safety_fallback` 卡必须保留该相对代价表述。
23. **验证信号逐信号标证据等级 + 来源平台**：`## 验证信号` 每条信号标注 `（证据等级: artifact_verified / tool_observed / agent_reported / inferred）+ 来源平台`；只有 `tool_observed`/`artifact_verified` 才算验证信号，`agent_reported` 不得当实测事实写进 `## 验证信号`（进 `## 误诊` 并如实标注）。
24. **未追到根因的卡，根因深挖列为 `## 遗留问题` 优先项**：`## 根因` 承认未追到底（如"TilingParse 未填充 CompileInfo 的确切机制未验证"）时，`## 遗留问题` 第一条必须把"复现并追根因到机制层"标为**优先项**（给下个 agent 明确的接续点），不得只写笼统 TODO。
25. **active 轨迹证据合同前置收集**：每个 adopted claim 必须有实际 normalized 路径、raw/normalized 两个完整 SHA-256、连续 coverage、与 `knowledge_form` 匹配的角色锚点、逐字机制 artifact、客观信号、双向 claim mapping 与单点归因。缺失必备项时明确 `provenance_missing`，候选只能作为 support；真实 fixed revision/blob 有则保留并优先，禁止伪造。

---

## 细粒度判定（一条 trace 应产 5~30 张，不是 1~6 张）

**目标**：以旧版 miner 为基准——同一批 trace 产 30 张细卡（`nddma-broadcast-input-blockoffset-misuse`、`int16-broadcast-datacopypad-below-min-copy-granularity`、`tanh-output-all-zero-tmpbuffer-missing`、`spec-formula-axes-input-stage8-typeerror`、`kernel-incremental-build-cache-stale`…一张根因一张卡）。

**分割单位 = 根因闭环**，逐事件扫描，不按"算子"或"主题"打包：

| 层级 | 判定 | 产卡规则 |
|------|------|----------|
| 失败信号 → 根因 → 修复 | 一个 `verify_failed`/编译错/报错 → 定位唯一根因 → 对应一次修复提交 | **一张卡**（信号/根因/配方/预防围绕同一根因） |
| 同一根因多次出现 | 同一错误码/同一切分层/同一条代码路径反复失败 | 合并成**一张卡**（`reproduce_count` 不虚构），不按轮次拆 |
| 一次失败里多个根因 | 一个失败输出里有两个不同归因（如"编译错 A"与"运行错 B"、公式错与词表错） | **各一张卡** |
| 一次修复动多处代码 | 修复 commit 改了 2 处独立缺陷（如 int16 搬运 + NDDMA offset） | **按根因拆两张卡**（各含自己的 before/after 段） |
| 成功实现里的独立技巧 | 每个可复用的 API/template/策略选择（如 bf16→fp32 Cast 通路、双缓冲、GetTanhMaxMinTmpSize） | **各一张 guide_card**（`task_recipe`/`optimization_recipe`/`debug_recipe`） |
| 环境/工具故障 | device unavailable / 权限 / 网络 / harness | **不产 kernel 卡**，进 meta 报告或 `debug_recipe`（若含工具用法） |

**操作规则**：
- **逐事件扫描，不抽样**：对 normalized_trace.jsonl（或 trace.json 的 turns）**逐条**过一遍所有 `verify_failed`/`tool_result` 中的失败输出、报错码、max_diff/mismatch、编译错误、超时；每个**唯一报错串/错误码/失败 case 组**就是一个候选入口。禁止"挑几个高价值点"式采样。
- **子 agent trace 必须纳入**：主 trace 里 `task` 派发的子 agent（`subagents/` 目录）是大量缺陷的藏身地（本批 30 卡中过半来自子 agent 的 kernel/联调循环）。扫描 = 主 trace 全部子 agent trace 的事件全量过一遍，子 agent 内部同样逐事件。
- **每张卡有唯一根因句**：草稿 `## 根因` 必须是**单句可判定**的归因（"广播维 stride=0 语义未实现"），若根因句出现两个"因为"则拆卡。
- **命名暗示粒度**：草稿文件名 `DRAFT-<area>-<n>.md` 的 `<n>` 按序递增，不按算子分组；正文 title 必须含根因要点（如"NDDMA 输入指针误加输出 blockOffset"），不得出现"XX 算子踩坑合集"式聚合 title。
- **错误码进 title（build 卡优先）**：现象有编译/运行报错码（如 `561002`/`507035`）时，**title 必须包含错误码**（如"ACLNN 561002 — GetCompileInfo null"）——落盘时 slug 会自动带上错误码，形成精确检索锚点；无错误码则用现象要点作 title。

**不合规示例（旧草稿会犯）**：
- ❌ 一张卡写"BenchGcd 广播/多核/大 shape 三件事" → ✅ 拆为 NDDMA 指针卡 + int16 搬运卡 + 561103 tiling 卡。
- ❌ 一张卡写"spec 公式问题"（含 INF 掩码 + BitAnd 白名单 + 词表）→ ✅ 各一卡。

---

## 输入契约

1. **归一化 trace**（miner 的标准输入）：
   - `session_manifest.json`（**先读这个**）：source sha256、adapter、coverage（unknown/redactions/skipped）、capabilities、event_types。
   - `normalized_trace.jsonl`（完整事件流，每行 `trace.event.v1`，带 provenance）：仅当需原文/原文代码时 drill-down。
   - **进入正文前**：核对 manifest 的 `unknown_events` 占比、`capabilities`（messages/tool_activity/file_changes/metrics 是否具备）；unknown 过多或能力缺失 → 在 `reconstruction.json` 记 limitations，候选相应降级。
   - **adapter 说明**：`markdown_transcript`（直接 ingest `parsed/context/ses_*.md` 转写）时，父会话与子 agent 各自独立 session；`unknown` 事件偏高或 `tool_activity` 缺失 → 该转写可能只含问答，候选相应降级或仅产 guide 配方卡。
   - 给目录则自动找这两个文件；给单个 `normalized_trace.jsonl` 则同目录找 manifest。
2. **兼容回退**：无归一化产物时，直接读 `trace_skeleton.json`（每 turn 含 `role/tool/preview/signals`）+ `trace.json`（完整，按需 drill-down）；此类候选在 manifest 的 `evidence_anchors` 以 `trace.json#<turn idx>` 为内部锚点并注明未过 normalize（不写卡正文）。由于缺少可解析的 raw provenance，兼容回退输出默认 support-only；须先补跑 normalize/verify 才能按轨迹原生证据合同发布。
3. **暂存输出**：`.build/ops-knowledge-trace-ingest/<YYYY-MM-DD>/<trace_id>/`（gitignored）。

---

## 重建（reconstruction.json，进入提取前必做）

读完整事件流后，先写 `.build/ops-knowledge-trace-ingest/<日期>/<trace_id>/reconstruction.json`：

```json
{
  "schema_version": "trace.reconstruction.v1",
  "source_sha256": "<完整64位 SHA-256>",
  "task": {"summary": "...", "operator": null, "unknowns": []},
  "phases": ["requirements", "implementation", "build", "runtime", "precision", "performance", "final_evaluation"],
  "facts": [{"claim": "...", "evidence_level": "tool_observed", "event_refs": [{"sequence": 142, "raw_source": "...", "raw_record": 143, "raw_sha256": "..."}]}],
  "assumptions": [{"claim": "...", "basis": "..."}],
  "unknowns": ["Case 9-20 未执行的真实原因"],
  "limitations": []
}
```

- `facts` 按证据等级标注（§证据等级）；`assumptions` 与 `unknowns` 分列，不混入 facts。
- 被拒绝/回退/无法归因的尝试与已接受尝试一并保留（防知识卡漏掉"坏实践"素材）。
- 该文件是 curator 的干净上下文输入之一；候选正文 `## 验证信号` 段首来源说明的事件引用从此处取得（不写卡片 frontmatter）。

---

## 证据等级（evidence_level）

| 等级 | 判定 | 候选用途 |
|------|------|----------|
| `artifact_verified` | 结果绑定到可重建源码状态 / 不可变产物（commit/快照/附件 hash） | 最强单跑证据 |
| `tool_observed` | 轨迹中有工具调用、命令输出、`verify_failed` 报错、profiling 数据 | 可进「## 验证信号」 |
| `agent_reported` | 只有 assistant/user 消息陈述该结果，无工具输出佐证 | 只进假设，**不能当实测信号** |
| `inferred` | 纯静态推断（无上板信号） | 不入主库，只 reject 或转 meta |

> 退出码为 0 只证明命令成功退出；文件 diff 只证明发生过改动；两者单独出现都不能证明正确性或性能。

---

## 代码开发轨迹重建（code-first，所有轨提取的前置）

**目标：从事件流恢复"agent 是怎么写/改/优化这段代码的"**——逐文件建立版本时间线，卡内所有代码块都必须能指到具体写入事件。四类代码证据事件：

| 事件 | 用途 |
|------|------|
| `file_write`（完整内容） | 恢复文件版本快照 v0/v1/v2…；**完整代码 = 终版写入内容（verbatim）** |
| `file_diff`/`edit` | 版本间差异；修复闭环的 before/after 边界 |
| `file_read`（完整内容） | 还原只读参照（模板/规格文件），供设计决策对比 |
| `bash`（cat/diff/git log 输出） | 补充被截断的写入事件（write 只落部分内容时） |

操作规则：

1. **逐文件建时间线**：对 trace 中出现的每个代码文件（`op_kernel/*.cpp`、`op_host/*.cpp`、tiling 头、spec.yaml、测试脚本、CMake…），按 sequence 收集其全部 `file_write`/`file_diff`/`edit` 事件 → 恢复 v0, v1, v2…；子 agent trace 同样处理（代码大多在子 agent 里写）。
2. **before/after 边界**：修复闭环中，before = 修复动作**前**最近一次完整写入；after = 修复后第一次完整写入（或终版）。二者均为**完整文件/完整函数**级（按函数边界截取并标注起止行号），禁止只留 1–3 行示意。
3. **完整代码 = 终版写入**：`## 完整代码` 与 guide 卡代码块一律取该文件终版 `file_write` 内容，verbatim 保留（不做语法润色、不补注释、不缩写）；仅当终版从未完整写入（只有 edit 碎片）时，用 diff 上下文组装并在卡内标注"部分恢复"，无法恢复的进 reconstruction unknowns，卡内标"代码未在 trace 中恢复"（HARD 约束 17 允许的标注）。
4. **设计决策素材** = 版本间 diff（哪个写法被换掉、回退轮次）+ reasoning 事件中"为什么"叙述（选型理由/备选/放弃原因）——「## 设计决策」必须有版本 diff 或 reasoning 证据支撑，禁止空谈。
5. **代码一律函数级完整内联**：涉及代码的卡，关键函数（before/after、`## 完整代码`）**一律正文内联为函数级完整代码块**，verbatim 取自事件流；**不因代码行长而外置附件**（附件外置已弃用——附件不进检索索引、卡不自包含）。
6. **产出对账**：每张候选卡的 `## 系统信息` 文件清单必须与事件流中实际读/写的文件一一对应，不凭空列文件。

## 反投机取巧（anti-shortcut，捷径不落库）

**"测试侧放松"捷径清单**（检测到任一即触发本纪律）：
1. 放宽 `numerical_tolerance`（rtol/atol 调松到恰好通过）；
2. 修改测试期望值/参考实现（gen_data.py/期望值/golden 脚本/比较器豁免如 hw_compat）；
3. 删减/禁用失败用例、把失败 case 从测试集剔除、skip/注释；
4. 把失败标注为"已知问题/环境问题"放行通过；
5. 换宽松 metric（max_relative→mean_relative/cosine）或降 dtype 绕过；
6. 固定随机种子/改输入分布让统计用例恰好过；
7. 只改测试不改实现（实现仍然错）；
8. 引用 trace 外记录（"前序 LOG.md/issue 记载、本 trace 未复现"）当验证信号（hearsay）。

处理规则：

- 该根因闭环**不产"解决配方"正卡**——即使 trace 中因此"通过"（HARD 约束 16）；
- trace 内**有真正代码修复** → 正常产代码卡，捷径作为该卡 `## 坏实践`/`## 误诊` 素材（"agent 先试了放宽容差/改期望，掩盖了真因；真正修复是 X"），并在 `## 验证信号` 只写代码修复后的实测；
- trace 内**只有捷径、无代码修复** → 不产 precision/build 正卡；捷径模式本身可复现可推广时，产一张按内部轨标记的负知识卡（`workflow_only`/`diagnostic` 轨，主题=防作弊：该捷径长什么样、为何掩盖缺陷、正确做法）；否则 reject 进 ledger/meta；
- **验证信号纪律**：`## 验证信号` 只收本 trace 内 `tool_observed`/`artifact_verified` 实测值；hearsay 最多进 `## 误诊` 并标注 `agent_reported`（HARD 约束 18）；
- `solution_layer: spec`/`test` 的候选须自证代码侧实质修复（如公式修正、掩码逻辑、测试脚手架 bug 修复），否则按捷径处理。

## 相关性预检（relevance gate，mine 入口必做）

**目的**：与 AscendC 算子生成/开发无关的日志（纯问答/闲聊/他领域任务）在进入任何 LLM 全量扫描前被拦截，避免时间与 token 浪费。**不用关键词匹配**（会遗漏语义相关但词面不典型的会话），改派**门禁子 agent** 做语义判断。

**调用**（reconstruction 与逐事件扫描之前）：
```text
Agent(references/subagents/ops-knowledge-trace-relevance-gate.md)
  输入：<normalize输出目录>（normalized_trace.jsonl + session_manifest.json）
  约束：门禁只读 trace 开头 ~60 事件（前 2~4 轮对话），禁止全量扫描
```

门禁 agent 熟悉 cannbot-skills 的三种 AscendC 算子开发流程（ops-registry-invoke 算子仓开发 / ops-direct-invoke Kernel 直调 / ops-direct-invoke-flash 核函数构建），按**任务意图 + 早期活动**语义判定：

| verdict | 判定 | 动作 |
|---------|------|------|
| `related` | 会话涉及 AscendC 算子生成/开发：用户要求生成/开发/适配某算子（含算子名/芯片）、在走算子生成工作流（spec.yaml/9-stage/DESIGN/TEST/wave1/wave2/CP）、早期活动触及算子工程（op_kernel/op_host/aclnn/tiling/编译/ST/UT）；**意图明确但仅启动也算 related**（宁放行勿误杀，价值预筛在扫描内兜底 0 张） | 继续 reconstruction + 逐事件扫描 |
| `unrelated` | 会话与算子生成无关：纯问答/闲聊、他领域任务、与算子无关的工具/流程调试 | **立即退出**（见下） |

**unrelated 退出产物**（零全量扫描，只写暂存目录 `.build/ops-knowledge-trace-ingest/<日期>/<trace_id>/`）：
- `relevance_gate.json`（门禁 verdict JSON，含 reason 与 confidence）；
- `reconstruction.json`：facts 记判定结论与依据，limitations 记"未深入扫描（相关性预检退出）"；
- `manifest.json`：`candidates: []`，`skipped: [{"reason": "not_ascendc_related", "claim": "<门禁 reason>"}]`；
- 不产 DRAFT、不建子 agent；curate 因 0 候选自动跳过（全流程直接以报告收尾）；图谱/知识库零改动。

**离线回归基准**（预期行为）：
- `ses_0a09f622`（long-tail 启动片段：任务=生成 LarsV2Update，已加载工作流/读需求，尚未动代码）→ **related**（意图明确），mine 后价值预筛产 0 张；
- 纯问答/闲聊/他领域 trace → **unrelated**，门禁后直接退出。

## 价值预筛（知识价值门槛，产卡前必过）

**每张候选在按根因闭环成稿前，先过四条价值判据**（runbooks-contract §0；一票否决，宁缺毋滥）：

| 判据 | 判定 | 不过的例子 |
|------|------|-----------|
| **垂域绑定** | 知识绑定 AscendC/NPU/工具链/评测机制的特有行为（API 语义、平台约束、编译/运行机制、tiling/搬运/精度规律） | "skill 按名加载失败就 glob 找路径"（任何工具链都适用）；"先读需求文档再动手" |
| **非显然性** | 根因/解法是下一个 agent 大概率踩坑或想不到的 | 重复加载失败 skill 2 次后发现要 glob（常识性探索，非垂域陷阱）；"报错先看日志" |
| **可复用性** | 有可迁移的完整配方/函数级代码/检查清单，或能改变下个 agent 行为 | 只有流程阶段描述（Stage 0→1→1.5）而无垂域结论；纯启动/编排过程记录 |
| **可验证性** | 有本 trace 内 `tool_observed`/`artifact_verified` 信号锚定；workflow_only 纯流程卡从严 | bash 结果未回、转写截断、仅 agent 叙述的闭环 |

**明确不产卡（直接记 `skipped`，不写草稿）**：
- agent 编排/加载重试/工具定位等**通用 LLM 行为**（`reason: domain_generic`）；
- **无垂域因果**的环境配置问题（skill 未注册、目录缺失、权限）——除非含垂域侧修复配方（`reason: no_domain_cause`）；
- **纯流程描述**、无失败-修复闭环的启动/编排记录（`reason: process_only`）；
- 转写不完整（无 `tool_result`、命令结果缺失）导致**无法验证**的闭环（`reason: unverifiable`）——最多进 reconstruction 的 unknowns；
- **与 AscendC 算子开发无关**（`reason: non_ascendc`）：通用软件工程坑（环境变量/锁文件/CMake 通用配置/文件权限）、工具操作步骤（msprof/dump/编译器/TTK 参数）、agent 工作流与治理、评测 harness 脚本问题、文档格式问题、**spec 校验规则类内容**——sancity 校验器/工具链自身的规则说明、spec schema 校验打回、与算子 kernel 行为无关的 workflow 规则（拿走后下个 agent 只在 spec 阶段被工具打回，不会踩 kernel 坑）一律不产卡——判定标准见 [`curating.md`](curating.md)「相关性判定」小节。**判别测试**：把知识从库里拿走，下个 Agent 写/调算子时还会不会踩同一个坑？"跑一遍/查文档/重装即解"的一律不产卡。弱相关候选（Agent/工具流程建议、不宣称 kernel 行为）按 `transfer_scope=workflow_only` 识别后**路由出库**（不落 runbooks 主库，只进 meta/ledger），不得以"勉强相关"身份落卡。

**操作**：逐事件扫描时对每个根因闭环先判价值，不过即 `skipped`（manifest 记录 reason），不进入草稿阶段；`manifest.json` 必须给出**产卡数与 skipped 数及原因**，供 curator 复核。产出 0 张候选是合法结果（启动片段/纯问答 trace 默认 0 张）。

## 四轨提取（主 agent 候选 A）

**先枚举后提取**：对全部事件（主 trace + 全体 `subagents/*/trace.json`）逐条建立"失败信号清单"，按 §细粒度判定把每个唯一根因闭环分配一轨，再逐卡填 §8 正文。四轨**等重、不可偏废**（勿因性能轨显眼而漏精度/工程，勿忽略成功实现里的可复用配方）：

**公共准入基线（四域通用，第一道闸，统一准入基准，runbooks-contract §0）**：每张候选的基准要求是**完整场景描述**——`## 现象`/`## 适用场景` 用自然语言讲清"在做什么（命令/步骤）、哪个算子哪个文件、看到什么报错（原文）、当时代码什么状态"，让人不看 trace 就能理解（纪律 15）；**禁止内部编号（Task N/轮次）与"Agent 转述"代替原始输出**；涉及代码的卡把关键代码**原样内联**（before/after verbatim 函数级，纪律 10/17）。基线不达标不进各轨提取：记 manifest `skipped`（reason=`missing_scenario`）。权威口径 = [`references/runbooks-contract.md`](runbooks-contract.md) §0「统一准入基准」。各轨在此基准上的记录内容：

### 精度轨 `precision_card`（错误现象，被动遇到）
- **来源**：`verify_failed` turn + `max_diff` / `mismatch` / NaN 信号；逐个失败 case 的 agent 分析+修复 commit；**多个失败 case 若为同一根因合并一卡，不同根因各一卡**。
- **现象判定**：
  - `output_all_zero`：`max_diff≈1.0` + 全 mismatch + 编译过无报错 → 指向 kernel 未执行/切分层，**非精度逻辑**。
  - `nan_inf`：输出含 NaN/Inf → 查 cast 上溢/除零/未初始化。
  - `partial_case_mismatch`：部分 case 错、特定 shape 错 → 查边界/tiling 尾块/广播搬运。
  - `bit_exact_drift`：小 `max_diff`、相对参考偏差 → 查精度策略/累加顺序。
- **`signal`** 填判别信号具体值（`max_diff=0.9998`、`mismatch=32768/32768`、`含NaN`）。
- **准入要点**：① 场景与错误现象（max_diff/mismatch/NaN/Inf/溢出）② 根因**机制链**（溢出/大数吃小数/相消/累加顺序/未初始化，含算式推导，纪律 16）③ 解决策略（精度策略/补偿算术/类型提升/重排）④ 验证信号。**仅"换随机种子/放宽容差"过 → 按反投机取巧处理**（§反投机取巧）。

### 工程轨 `build_card`（编译/运行，被动遇到）
- **来源**：编译报错 / runtime 报错 / 超时 / 资源超额的 turn + 修复；**一个报错串一个根因 → 一张卡**（如"spec-yaml 缺必填字段""GetWorkspaceSize 561103 因 tiling 未实现"分卡）。
- **现象判定**：`compile_failure`（模板实例化/API 不支持/语法）/ `runtime_error`（段错误/越界/断言）/ `hang`（死循环/同步死锁/超时）/ `resource_exceeded`（UB/GM 超额）。
- **`signal`** 填报错信息/错误码关键片段。
- **准入要点**：① 场景完整描述（命令/工具链/报错**原文**/错误码）② 根因（编译/运行**机制层**归因）③ 代码或配置级修复 before/after（函数级完整代码）④ 验证信号（编译过/运行通过）。**缺原始报错输出或"重装/改路径即解"不产卡**。

### 性能轨 `perf_card`（profiling 信号，主动观测）
- **来源**：`__STATE`/STATE 阶段 profiling + 逐轮 diff + 加速比 Δ。
- **现象判定**：`below_compute_capacity`（整体慢，IU/带宽均低）/ `bandwidth_unsaturated`（搬运瓶颈、DMA stall）/ `iu_underutilized`（计算未吃满）/ `shape_axis_slow`（特定 shape/轴慢）。
- **`signal`** 填 IU%、带宽利用率、加速比、Δ。
- **口径纪律**：STATE 单跑自评 vs 标准化 `tasks_eval` 几何平均不可混淆——单跑只标 `single_run`，不可臆称 verified；绝对单跑值只进 provenance，不写成通用预期收益；同一算子内部两条路线的**相对**性能代价可进 `## 验证信号`/`## 性能影响`（标注参照路线+来源平台，纪律 22）。
- **准入要点**：① 场景 + profiling 信号（IU%/带宽/加速比 Δ，注明 profiling 来源）② 性能手段清单（哪些手段/策略提升性能、哪些**无效**）③ **精度未退化证据**（同 shape 精度 N/M 通过或 max_diff 不变；**未验证精度须显式标注"未验证精度影响"**）④ 相对代价成对表述。**只报性能不报精度 → 按"未验证精度"降级或拒**。

### 方案轨 `guide_card`（完整配方，从成功实现/系统性做法提取）
- **来源**：agent 成功完成任务的完整实现流程；可复用的工具/调试/构建流程；被反复验证的模板代码。
- **现象判定**：
  - `task_recipe`：完整任务实现配方（如"多核切分 kernel 骨架"）。
  - `optimization_recipe`：完整优化配方（含测量方法 + before/after 完整代码）。
  - `debug_recipe`：系统化排障配方（含工具链用法 + 可执行诊断脚本/命令）。
- **提取要求（学习 trajectory 的"系统知识"标准）**：候选必须包含 **`## 系统信息`**（toolchain/版本/目标平台/目录布局/相关文件清单，与事件流实际读写一一对应）、**`## 完整代码`**（**可执行、可复用的完整实现或诊断脚本，verbatim 取自终版 `file_write`、正文内联，不因行长外置附件**）与 **`## 设计决策`**（设计理由、备选与权衡、被放弃的设计，须有版本 diff 或 reasoning 证据）。**这是本轨与现象卡的本质区别：现象卡给"怎么修"，guide 卡给"完整怎么做的系统解法 + 为什么这么做"。** frontmatter `platforms` 为必填：目标平台能定位时写词表取值，无法定位写空表 `[]`（不伪造）。
- **准入要点**：三段齐全——系统信息/完整代码可执行/设计决策（缺一按缺段退回补全或 reject）。

### 设计决策提取（代码设计知识，所有轨通用）

从 trace 的 design/implementation 阶段事件（agent 的 reasoning、tool_call 参数里的代码草稿、read/write 的迭代 diff）中提取代码设计知识：
- **设计理由**：为什么选该 tiling 切分/block 循环/单双缓冲/buffer 深度/API/template（如"块循环保搬运连续度"）；
- **备选与权衡**：讨论过但未采用的设计（如原子计数 vs 块循环、双缓冲 vs 单缓冲），以及放弃原因（同步开销/复杂度/收益不足）；
- **被放弃/回退的代码**：`file_write` 回退轮次的内容是"坏实践"与"设计决策"的原始素材。

> **遗留问题提取**：从"本卡未解决的遗留问题 / 未验证的替代设计 / 性能未达标时的下一测量点 / 遗留 TODO"中提取 `## 遗留问题`——给下个 agent 的接续点，有则必写，无则标"未尝试"。**未追到根因的卡，第一条必须是"复现并追根因到机制层"优先项**（纪律 24）。

> **精度/工程轨从 `verify_failed`/报错提取；性能轨从 STATE profiling 提取；方案轨从成功实现/工具流程提取**——提取方式不同，但统一为 `phenomenon` 检索键。

### 子 agent 全覆盖（细粒度的产量来源）

主 trace 里 `task` 派发的每个子 agent 都有独立 `trace.json`（`<trace>_<ses>/subagents/<ses>/`）。它们承担 kernel 编码/联调/UT、spec 生成/自审、缺陷修复等大头，**大部分根因闭环在子 agent 里**。扫描规则：

1. **全量枚举**：主 trace `turns` 中每个 `tool_call.name==task` 的参数 `description/task_id` → 找到对应 `subagents/<task_id>/trace.json`；**逐个**其事件流扫描，不遗漏、不挑代表性。
2. **同样逐事件**：子 trace 里每个失败信号（编译错/报错/verify FAIL）同样按"根因闭环"产卡，manifest 的 `evidence_anchors` 使用子 trace 事件的 `sequence/event_type/raw_source/raw_record/raw_sha256` 作内部锚点（不写卡正文）。
3. **关联到主 trace**：manifest 的 `evidence_anchors` 同时记主 trace 派发 turn 与子 trace 内部 sequence，便于 curate 内部核验。
4. **不因主 trace 无失败而跳过**：子 agent 的失败/修复闭环独立成卡（主 trace 可能只看得到 task 调用的成功返回）。

> 子 agent 目录缺失或 task_id 对不上时：记入 `reconstruction.json` 的 `limitations`，并降级为仅凭主 trace 可见信号作卡（证据等级上限 `inferred`，不产候选卡）。

每条候选蒸馏 `症状 / 适用场景（必填：工程形态/API 路径/验证平台与版本/适用粒度/路线优先级/不适用场景）/ 根因（区别误诊）/ 配方（before·after）/ 系统信息 / 完整代码（guide 必填）/ 性能影响（有性能故事时）/ 预防 / 验证信号（逐信号标证据等级+来源平台）/ 失效边界（含"未验证，推断可迁移"标注）/ 坏实践 / 误诊（可选）/ 遗留问题（未追根因时优先项）`（对应 runbooks-contract §8 正文）。**`症状` 按纪律 15 场景还原（自然语言讲清"在做什么/看到什么报错/代码状态"，禁内部编号代替）；`配方` 按纪律 17 展示 before/after 实际代码形态（禁只给 commit id）；`适用场景` 按纪律 19-23（场景/路线/platforms/相对代价/证据等级）**；并判定 `solution_layer`（配方作用在哪层：kernel 切面 `tiling`/`kernel`/`multi_template`/`precision_strategy`，或流水线产物层 `spec`/`op_host`/`test`/`build_system`，guide 流程类用 `workflow`；按"改的文件"判定——`op_kernel/*.cpp` 归 kernel 切面，`op_host/*.cpp`/spec.yaml/测试脚本/CMake 归流水线层）。

---

## 证据 → 候选（字段映射，主 agent 候选 A）

每条候选严格按 `runbooks-contract.md` §3 frontmatter + §8 正文产出，miner 阶段的特殊取值：

| 字段 | miner 取值 |
|------|-----------|
| `type` | `"Runbook"`（由路径 Profile `runbooks` 决定，不手工另设）；内部四轨 `precision_card`/`build_card`/`perf_card`/`guide_card` 是提取分类，只进 manifest，落盘时映射 area：build→`compilation`、precision→`precision`、perf→`performance`、guide→`compilation`/`runtime`（由 curate 按内容判定） |
| `knowledge_form` | **只进 manifest，不写卡 frontmatter**：`repair_recipe`/`diagnostic_rule`/`negative_result`/`validated_pattern`，决定 §8.1 的 evidence roles 与正文主章节 |
| `phenomenon`/`signal`/`solution_layer` | **只进 manifest**（聚类与证据角色用，不写卡 frontmatter）；frontmatter 只保留注册 `tags` |
| evidence_level | **不设 frontmatter 字段**：证据等级（`artifact_verified`/`tool_observed`/`agent_reported`/`inferred`）记入 manifest（`evidence_anchors`），供 curator 判定 tier（§5）；**不写进卡正文** |
| `reproduce_count` | **只进 manifest/ledger**（单条 trace 默认 1），不写卡 frontmatter |
| `platforms` | **必填**：**只填 trace 内实际验证过的平台**（芯片名/AddConfig soc 名/探测结果 + 上板或可运行实测），取受控词（以 本仓平台词表（`registries.yaml`） 注册值为准：`950`/`a3`/`a2`）；无法定位则写空表 `[]`（不伪造；缺省不代表通用平台）；推断可迁移的平台写入 `## 失效边界` 并标注"未验证，推断可迁移"（纪律 21） |
| 迁移边界 | **不设 frontmatter 字段**：跨算子纪律默认生效（禁源算子常量/checkpoint/shape 列表/绝对单跑分数）；适用粒度与具体边界写正文 `## 适用场景`/`## 失效边界`（runbooks-contract §8/§11） |
| `evidence`（frontmatter） | **不设**（runbooks-contract §11）：溯源锚点（`sequence/event_type/raw_source/raw_record/raw_sha256`，取自 reconstruction 的 event_refs）只进 manifest 的 `evidence_anchors`，**不写卡正文** |
| `## 相关`（正文末） | **不建**（miner 不建反链；curator 落盘时在正文末加 `## 相关` + markdown 超链接，见 runbooks-contract §7；同问题域冲突/方案关系由 curator 双侧标注） |
| `timestamp` | 取系统时钟（`date`），不臆造 |
| 正文 `## 验证信号` | 如实记 R<n> + 精度 N/M / Δ / 编译通过，**每条信号标注来源平台 + 证据等级**（如"精度 32768/32768 通过（dav-2201，tool_observed）"）；仅 `agent_reported` 则标"非实测·仅叙述"并**不得写入验证信号**（进 `## 误诊`），或标"无上板信号·inferred" |
| 正文 `## 适用场景` | **所有卡必填**：工程形态/API 路径/验证过的平台与 CANN 版本/适用粒度（transfer_scope 五档取最窄）/路线优先级（recommended_fastpath|safety_fallback|banned）/明确不适用或未验证场景；`safety_fallback` 卡必须明写 fallback 声明（纪律 19-20） |
| 正文 `## 性能影响` | 有性能故事时必填：同一算子内部两条路线的相对性能代价（如"相对 SIMT 路线约 0.05x"，标注参照路线+来源平台）；禁绝对分数、禁通用预期收益（纪律 22） |
| 正文 `## 系统信息` / `## 完整代码` | 完整配方类 runbook 必填（guide 轨）；现象卡有完整可复用代码时也鼓励补全 |
| 正文 `## 设计决策` | 完整配方类 runbook 必填；现象卡涉及设计取舍（tiling/buffer/API/template）时必填——**强制记录①为何选这套方案②放弃的候选及原因③当前方案属哪档路线**（纪律 9/§设计决策提取） |
| 正文 `## 遗留问题` | 本卡未解决的遗留问题/接续方向；无则标"无"；**未追到根因的卡把根因深挖列为优先项**（纪律 24） |
| 正文 `## 验证信号` 段首来源 | 验证信号段首先用自然语言写问题与验证来源（哪次开发会话/修复步骤/实测结果）；**不写内部结构化锚点**（锚点只进 manifest 的 evidence_anchors） |

> **无 `id`/`resource` 字段**（见 runbooks-contract §3）：草稿唯一性由文件名 `DRAFT-<area>-<n>.md` 保证；正式 slug 文件名由 curator 落盘时定。

---

## 跨算子纪律（候选阶段即生效）

- 跨算子纪律默认对全部候选生效：**不得包含**源算子 checkpoint、代码常量、shape 列表、**绝对**单跑分数（score/latency/speedup 绝对值）——绝对单跑数值只作 manifest 内部记录（provenance），不写成通用预期收益。
- **相对性能代价允许**：同一算子内部两条路线的成对相对对比（如"相对 SIMT 路线约 0.05x"）可进 `## 验证信号`/`## 性能影响`，必须标注参照路线与来源平台；禁单独报绝对分数、禁写成通用预期收益（纪律 22）。
- 根因是环境故障（device unavailable/quota/网络/harness）的候选**不落 kernel 卡**：若整条知识都是环境问题 → 只进 meta 报告；环境噪音但其中含 kernel 因果证据 → 只提取 kernel 部分。

---

## 完整代码提取（从事件流恢复可复用代码，code-first 的落点）

从 `tool_call`（read/write/edit 参数含 file_path + 完整内容）与 `tool_result` 事件中恢复（细节见 §代码开发轨迹重建）：
- **文件清单**：`file_read`/`file_write`/`file_diff` 事件的路径集合 → `## 系统信息` 的相关文件清单（与实际读写一一对应）。
- **before 代码**：修复轮次前最近一次 `file_write`/`file_diff` 事件里的**完整函数/文件**内容。
- **after 代码**：修复轮次后终版 `file_write` 事件内容（或 `tool_result` 里的 diff 快照），verbatim 保留。
- **可执行脚本**：`bash` 工具参数里的诊断命令/脚本 → `debug_recipe` 的复现命令（完整给出）。
- **机制完整底线**：repair 的 before/after 必须完整；diagnostic/negative/validated 分别保留可执行 probe、可重建尝试或完整实现及对应原始观测。卡内 artifact 只准来自事件流，不准凭记忆重写；核心证据恢复不全则 defer。**一律正文内联，不设附件外置通道**。

---

## 输出格式

暂存目录 `.build/ops-knowledge-trace-ingest/<YYYY-MM-DD>/<trace_id>/`：

```
├── manifest.json              # 本次挖掘清单：trace_id + 候选列表 + 各候选路径/轨/evidence_level
├── reconstruction.json        # 事实/假设/未知 + event_refs（curator 的干净上下文输入）
├── DRAFT-precision-01.md      # 每个根因闭环一个草稿卡（runbooks-contract schema 合规；编号按顺序递增）
├── DRAFT-precision-02.md
├── DRAFT-build-01.md
├── DRAFT-build-02.md
├── DRAFT-build-03.md
├── DRAFT-perf-01.md
├── DRAFT-guide-01.md
└── ...                       # 完整代码一律内联在草稿正文，无附件外置（机制已弃用）
```

> **数量预期**：一条含 kernel 联调 + spec 生成的**完整开发 trace** 应产 **≥10 张**候选（旧版同源 5 trace 产 30 卡）；**启动片段/纯问答 trace 产出 0~2 张为正常**（先过 §价值预筛）——若一条完整 trace 只产 1~3 张，说明扫描抽样或把多根因合并了（违反纪律 0）；若产出大量低价值卡（agent 编排/流程描述），说明没过价值门槛（违反纪律 12）。

- 每个草稿卡 = 完整 frontmatter + 正文，**schema 合规**（跑 `runbooks-contract` validator 时除文件名 `DRAFT-*` 非纯 slug 与「## 相关」可空外，其余约束全过）。
- `manifest.json` 记每条候选的 `{draft_path, type, knowledge_form, phenomenon, solution_layer, evidence_level, evidence_roles, mechanism_artifacts, signal, normalized_trace_path, raw_source_sha256, normalized_trace_sha256, coverage, claim_mapping, provenance_missing:[...]}`，供 curator 读。`evidence_roles` 的键按 runbooks-contract §8.1 随形态变化；artifact 逐字内容、重建方式与角色锚点必须结构化记录。**另须记 `skipped` 清单**并对旧式修复门禁 skip 写 `reclassification_checked: true`，供 curator 与 meta 报告对账。

---

## 不做什么（职责边界）

- **不写 `knowledge/ops/ascendc/runbooks/`**（落库是 curator 的事）。
- **不改任何 `index.md`**。
- **不做去重 / 新颖性审查**（不读现有 runbooks 库）。
- **不升级 `verified`**（不编造复现计数）。
- **不建 「## 相关」反链**（留空）。
- **不整体重写**（本 skill 只新建草稿，无旧卡可改）。
- **不把 `agent_reported` 当实测**（证据等级纪律）。

---

## 与 curator 衔接

```
trace ──normalize──▶ 归一化事件流 ──▶ mine ──▶ reconstruction.json + 暂存草稿卡 + manifest.json
                                                                                │
                                                                                ▼
                                        curate：门控（证据锁）+ 独立审查 + 新颖性/去重 + 落盘 knowledge/ops/ascendc/runbooks/ + index/相关/ledger
```

- **默认自动衔接**：全流程模式下（SKILL.md §阶段切换），mine 产出候选后**立即自动进入 curate ingest**（主 agent 继续执行门控/审查/落库/统一收口），不在 mine 后停下等指令；**mine 产出 0 张候选（价值预筛合法剔除）→ 跳过 curate，直接以报告收尾**（skipped 清单即产物）。
- miner 也可独立跑、攒一批草稿再交 curator 统一策展（批量模式），天然支持跨会话去重与复现计数升级——仅当用户显式要求攒批时使用。

---

## 验证（离线单测）

1. **dry-run trace → 候选表**：对照 hand-built 期望（各失败 case + perf 各轮 + 成功实现 + **子 agent 闭环** → 预期 phenomenon/solution_layer 映射）。
2. **细粒度（量）**：候选数 ≥ 期望值（同源批 30 卡基准）；**无聚合卡**——每卡 `## 根因` 是单句可判定归因（不出现两个"因为"），title 不出现"合集/汇总/踩坑"字样。
3. **schema 合规**：草稿卡跑 `runbooks-contract` validator，除文件名 `DRAFT-*` 非纯 slug 与「## 相关」可空外全过（含必填 `platforms`、guide 卡含系统信息+完整代码+设计决策）。
4. **门控有效**：仅 `agent_reported`/`inferred` 证据的候选**不入主库**（tier 由 curator 按 §5 判定），**不产 `verified`**。
5. **无泄露**：草稿卡 frontmatter/正文/文件名均无 session_id 与内部结构化锚点（source/raw record/sequence 只进 manifest）。
6. **四轨覆盖**：精度/工程/性能/方案四类均扫到，无一缺席。
7. **证据可溯（内部）**：manifest 每条候选的 `evidence_anchors` 均能在 normalized_trace.jsonl（或子 trace）按 sequence 找到，且 `raw_source/raw_record/raw_sha256` 与事件 provenance 一致；卡正文无内部锚点引用。
8. **足量覆盖**：抽查每条候选对照 runbooks-contract §8 维度表，what worked/failed/root cause/lessons/strategy/avoid/code design/code 有证据即写、`## 遗留问题` 有接续即写、`## 设计决策` 有设计讨论即写——无静默留空。
9. **子 agent 覆盖**：`manifest.json` 候选集的 `evidence_anchors` 覆盖主 trace + 全部可解析子 trace；有子 trace 未扫时会列出 limitations。
10. **门禁职责隔离**：门禁子 agent 只做相关性判定（§相关性预检），其调用记录无 runbooks 库读取、无挖掘行为。
11. **代码完整（code-first）**：抽查每条涉及代码改动的候选——before/after 为**函数级完整代码块、正文内联**（无 1–3 行示意、无附件外置）；正文代码能在事件流中找到对应 `file_write`/`file_diff` 事件（`## 验证信号` 段首来源可溯）；guide 卡完整代码可执行。
12. **价值门槛**：抽查候选与 `skipped` 清单——无常识性/agent 编排/纯流程类草稿被产出（`skipped` 的 reason 合理）；启动片段 trace 产出 0 张不判违规。
13. **反投机取巧**：无任何候选把"放宽容差/改测试/改期望/删用例"当解决配方（正知识）；`solution_layer: spec`/`test` 的候选均有代码侧实质修复；`## 验证信号` 无 hearsay（无"前序 LOG.md 记载/本 trace 未复现"字样）。
14. **相关性预检**：mine 入口已派门禁子 agent（`subagents/ops-knowledge-trace-relevance-gate.md`），其读取范围 ≤ trace 开头 ~60 事件；unrelated trace 产出 `relevance_gate.json` + `manifest.json`（candidates=[]、skipped=not_ascendc_related）且**无任何 DRAFT**；related trace（含意图明确仅启动者）正常进入扫描。
15. **active 轨迹证据合同显式**：每条涉及代码的候选都在 manifest 给出完整 `code_evidence`、修复前后信号锚点与 claim mapping，或列明必备的轨迹原生证据 `provenance_missing` 并标为 support-only；不得因仅缺 remote blob 而 defer，也不得交给 Curator 猜 URL 后发布。
16. **适用场景必填**：每张草稿含 `## 适用场景`（工程形态/API 路径/验证平台与版本/适用粒度/路线优先级/不适用或未验证场景）；`safety_fallback` 卡含明示的 fallback 声明；路线三档与正文 `## 设计决策` 一致。
17. **platforms 严格**：frontmatter `platforms` 只含 trace 内实际验证平台；推断可迁移平台在 `## 失效边界` 标注"未验证，推断可迁移"，未混入 `platforms`。
18. **相对代价纪律**：无绝对 score/latency/speedup 落卡正文（provenance 只进 manifest）；相对性能代价成对出现并标注参照路线与来源平台。
18. **验证信号逐信号标注**：每条信号带来源平台 + 证据等级（`tool_observed`/`artifact_verified`）；`agent_reported` 未混入 `## 验证信号`。
19. **未追根因 → 优先项**：`## 根因` 承认未追到底的卡，`## 遗留问题` 第一条有"复现并追根因到机制层"优先项。