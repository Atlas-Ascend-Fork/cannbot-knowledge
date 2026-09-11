---
name: ops-knowledge-trace-ingest
description: 把一次算子开发会话的原始记录（日志目录 / trace 目录 / 轨迹导出 / 可读转写）自动整理成可检索的 runbook 实战知识卡：按证据形态提取修复配方、诊断规则、失败路线与已验证模式，保留现象、信号、机制、适用边界和客观验证，并带来源溯源落到 runbooks/。输入日志目录或轨迹即可全自动跑通；也可只解析、只挖草稿、只落库，或在用户明确授权时清空并全量重建 runbooks。触发：用户说"解析日志""从这条 trace 挖 runbooks""把草稿落库""跑一次复现升级""清空 runbooks 从轨迹重建"。手动触发。
---

# ops-knowledge-trace-ingest：trace → runbooks 端到端摄入

把一条算子开发会话从**原始来源**到**落库 runbook 卡**的全流程收进一个 skill，分四阶段，按输入自动选阶段；用户也可直接指明只执行某一阶段：

```
会话日志/转写 ──parse──▶ trace 目录 ──normalize──▶ 归一化事件流 ──mine──▶ 候选草稿 ──curate──▶ knowledge/ops/ascendc/runbooks/<area>/
（0 LLM）                          （0 LLM，溯源/脱敏/coverage）   （LLM 挖掘）      （LLM 门控+审查落库）
```

各阶段做什么、产出什么：
- **parse（解析）**：把原始日志/转写整理成结构化 trace 目录（每事件一条记录）。产出：trace 目录。
- **normalize（规整）**：统一事件格式、剥离敏感信息、统计覆盖度。产出：归一化事件流（可审计、可溯源）。
- **mine（挖掘）**：从事件流里找出有知识的修复、诊断、失败边界和已验证模式闭环，写成候选草稿卡。产出：`DRAFT-*.md` 候选草稿。
- **curate（策展落库）**：候选卡过门控（去重/相关性/价值）→ 独立审查 → 落库到 `knowledge/ops/ascendc/runbooks/`。产出：正式 Runbook 卡 + 当日日志。

## 何时用

用户说任一：
- "解析 / 规整算子开发会话日志 / 这堆 session 日志整理成可读的" → **parse**
- "把这条 trace / 轨迹导出规范化、去敏、出审计清单" → **normalize**
- "用这条 trace 挖一下 runbooks / 从这次算子开发会话抽知识" → **mine**
- "把挖出来的草稿落库 / 策展现场笔记 / 升级 runbooks / 跑一次复现升级" → **curate**
- "处理 / 摄入 / 走一遍这条 trace（会话）" → **全流程 normalize→mine→curate**

> **默认端到端**：给任何 trace 类输入（日志目录 / 转写 md / 轨迹导出 / 归一化目录）时，**默认执行完整流水线**（parse|normalize → mine → curate 落库），不中途停下等指令；只有当用户明确只要某一阶段（如只说“解析”“挖一下”）时，才停留在该阶段。全流程下：mine 产出候选 → 自动接 curate ingest（门控 + 独立审查 + 落库 + 统一收口）；**mine 产出 0 张候选（价值预筛合法剔除）→ 跳过 curate，直接报告**（§完成报告含 skipped 清单）。

## 阶段切换

按输入类型自动推断**起点**；**默认跑完剩余全流程**（parse→normalize→mine→curate），用户指名单阶段时停在指定阶段：

| 输入 | 推断起点 | 默认动作 |
|---|---|---|
| 单个 `session=ses_*/` 目录 **或** 含多个 `session=ses_*/` 的父目录 | parse | 跑 `scripts/parse.py`（自动识别单/多）→ 继续 normalize→mine→curate |
| 任意轨迹导出（JSON/JSONL/NDJSON/文本/zip/tar/`-`）**、** 算子开发会话 `parsed/context/ses_*.md` 可读转写（单文件或整目录）** 或 ** trace 目录（含 `trace.json`）| normalize | 跑 `scripts/trace_normalize.py`（自动检测适配器：`trace_export`/`generic`/`markdown_transcript`/`claude_code`/`opencode`/`codex`）→ 继续 mine→curate |
| 归一化目录（含 `normalized_trace.jsonl` + `session_manifest.json`）| mine | 门禁子 agent → 派 `ops-knowledge-trace-miner` 挖 reconstruction + 候选草稿 → 有候选自动接 curate；0 候选直接报告 |
| 草稿目录（含 `DRAFT-*.md`/`manifest.json`）或 `upgrade` | curate | curator 产 pending ledger → 主 agent 生成 staged cards → reviewer 独立审查并签 receipt → 主 agent 收口落库 / 复现升级 |
| **批量目录**（`parsed/context/**` 下大量 `ses_*.md`）| batch | `trace_normalize.py batch`（多进程）→ 门禁扇出 → mine 扇出并行 → 预聚类 → curate 聚合 → 收口（§批量模式） |

`parse`/`normalize`/`mine`/`curate`/`batch` 与 `ingest`/`upgrade`/`rebuild` 是主 agent 的编排阶段和模式名，不是统一 CLI 参数；只调用各脚本自身 `--help` 声明的参数。`rebuild` 只允许在用户明确授权全量清空时启用。

## 不变量（违反即废）

1. 每个规范化事件和知识结论都能回溯到来源 hash 与记录位置（`provenance.raw_sha256` + `raw_source` + `raw_record`）。
2. 不得静默丢弃事件：必须规范化、标 `unknown` 或记录明确的跳过理由（coverage 对账）。
3. 工具输出的可信度高于 Agent 叙述；仅 `agent_reported` 的结论只能当假设，不能当实测信号。
4. 原始时间线只进 `.build/` 与暂存区；知识卡只写蒸馏后的系统知识。
5. 单条轨迹最高只能得到内部 tier `single_run`；内部 tier `verified` 必须跨轨迹复现（≥2）且证据等级 `tool_observed`/`artifact_verified` 且 `## 验证信号` 含上板实测信号。这一 tier 只存 ledger/manifest，不是 frontmatter `verified`；后者只能记录真实 `{by, at}` OKF verification event。
6. 全部 runbook 卡（跨算子纪律默认生效）禁止含源算子常量/checkpoint/shape 列表/**绝对**单跑分数；同一算子内部两条路线的**相对**性能代价允许（标参照路线+来源平台，见 runbooks-contract §6-9）。
7. 不得猜测缺失的任务、环境、源码或评测信息；统一记录为 unknown。
8. index、ledger、coverage 与 log 由 curate 的**统一收口**（单一 finalizer）一次性写入，禁止分散零散修改；需要的跨卡引用直接写为普通正文链接，不触发图谱流程。
9. 环境/工具故障（device unavailable/quota/网络/harness）默认不写成 kernel 知识，只进 meta。
10. 只要求原始来源，不要求用户说明 Agent 类型/提供 manifest；格式由脚本自动检测。
11. **形态化机制证据（内部 taxonomy）**：挖掘分类（`repair_recipe`/`diagnostic_rule`/`negative_result`/`validated_pattern`）只进 manifest/ledger 等 `.build/` 中间产物，不写卡 frontmatter；再按 runbooks-contract §8.1 取证。`repair_recipe` 需要失败/完整因果单元 before/after/修后验证；`diagnostic_rule` 需要触发/探针/观测/判别；`negative_result` 需要尝试/客观失败或回退/边界；`validated_pattern` 需要完整实现单元/验证。只有修复配方强制 before/after；其余形态不得仅因没有成功修复或完整外层函数而 defer。所有核心代码/配置仍须 verbatim、正文内联，禁止示意片段和叙述补写。
   - 本地未提交轨迹使用 runbooks-contract §8.1 `trace_snapshot`：ledger 显式记录实际 normalized 路径、`raw_source_sha256`、`normalized_trace_sha256`、连续 coverage 和形态化角色锚点；两个 SHA 命名空间不得互比。核心机制 artifact 须由完整快照或无缺口 edit 链逐字恢复。
   - Issue/PR、固定上游版本或 API 规范主张使用 `fixed_source`：40 位 revision 与精确 blob 证据；不得用轨迹快照替代规范来源。
12. **反投机取巧**：放宽容差/改测试/改期望/删用例等"测试侧放松"不得作为修复配方或已验证模式；若轨迹客观证明其危害，可作为明确 `banned` 的 `negative_result`。`## 验证信号` 只收本 trace 内实测，trace 外 hearsay 不得进入。
13. **知识价值门槛（宁缺毋滥）**：候选必须垂域绑定（AscendC/NPU/工具链特有行为）+ 非显然 + 可复用 + 本 trace 内可验证（runbooks-contract §0）；agent 编排/工具定位等通用行为、无垂域因果的环境问题、不满足任一知识形态的纯流程描述、转写截断无法验证的闭环、与算子开发无关的工具/工作流/harness 坑（`non_ascendc`）→ **不产卡**（manifest `skipped` 记 reason）。**启动片段/纯问答 trace 产出 0 张是合法结果**。
14. **相关性预检（relevance gate）**：mine 入口先派**门禁子 agent**（`references/subagents/ops-knowledge-trace-relevance-gate.md`，熟悉 cannbot-skills 的三种 AscendC 算子开发流程（ops-registry-invoke / ops-direct-invoke / ops-direct-invoke-flash），只读 trace 开头几轮）语义判断会话是否涉及算子生成；**`unrelated` 立即退出**（只写最小化退出产物，不 LLM 扫描、不产草稿）；`related`（含意图明确仅启动的会话）继续，价值预筛兜底 0 张——无关日志零浪费，且不靠关键词匹配（防遗漏）。
15. **active 轨迹证据合同前置**：由开发轨迹生成的 active `single_run` 须满足 runbooks-contract §8.1：每个 adopted claim 有两个来源 SHA-256、可解析 raw record/sequence 锚点、与内部 `knowledge_form` 匹配的角色锚点、逐字机制 artifact、客观 `tool_observed|artifact_verified` 信号、双向 claim mapping 和单点归因。Mine 必须把合同写入 manifest/reconstruction，缺失项列 `provenance_missing`；固定 revision/blob 有则保留并优先，无 remote/blob 不得单独导致 defer，也不得伪造链接。

## 阶段 1 · parse（原始日志 → 可读 trace，0 LLM）

```bash
python3 <SKILL_DIR>/scripts/parse.py <日志目录> -o <trace输出目录>
```

- **输入**：单个 `session=ses_<MAIN>/` 目录（直接传，自动识别）或含多个 `session=ses_*/` 的父目录。布局 `session=ses_*/YYYY-MM-DD/ls.s3.*.partN.txt`（会话日志原始格式，JSONL，每行一次 LLM 调用）。
- **产出**：`trace_<ses>/` 下 `trace.json`（结构化 turns）/ `trace.md`（人类时间线）/ `tree.txt`（子 agent 调用树）/ `summary.json` / `attachments/`（>2KB 内容外存）/ `subagents/`。
- **关键不变量**：`messages` 累积式（取 `len(messages)` 最大的行作 canonical 快照）；SSE 响应按 `index` 聚合 `tool_calls`；子 agent 关系按目录嵌套判。
- 流式解析，100MB+ 不全量入内存；155MB/7 session ~1.2s。

> 详见 `scripts/parse.py` 顶部 docstring（算法 5 阶段 + 陷阱）。

## 阶段 2 · normalize（任意轨迹 → 归一化事件流，0 LLM）

```bash
python3 <SKILL_DIR>/scripts/trace_normalize.py normalize <trace目录或轨迹导出> --output <build>/trace-normalized/<sha12>
python3 <SKILL_DIR>/scripts/trace_normalize.py verify <输出目录>        # 确定性校验，必须 ok
```

- **输入**：parse 产出的 `trace_<ses>/` 目录（adapter=`trace_export`），或任意 Agent 轨迹导出——JSON/JSONL/NDJSON/文本/zip/tar/目录/`-`（adapter=`generic`，自动检测），或 算子开发会话 `parsed/context/ses_*.md` 可读转写——单文件或整个 `parsed/context/` 目录（adapter=`markdown_transcript`；支持 `## Subagent Sessions` 多会话转写，父会话与子 agent 各自独立 session）。**主流 agent 框架专项适配器**：Claude Code `~/.claude/projects/<project>/<session>.jsonl`（adapter=`claude_code`，现代 block 数组 + 旧 flat 记录双格式）、opencode session JSON（数组或 `{messages:[...]}`，adapter=`opencode`）、Codex `~/.codex/sessions/<date>/<session>.jsonl`（adapter=`codex`）——直接喂框架导出即可全自动，无需手工转 markdown（opencode 适配器目前经合成 fixture 验证；真实导出建议先 `detect` 核对 adapter 与 coverage 再 full-run）。
- **产出**：`normalized_trace.jsonl`（每行一个 `trace.event.v1` 事件：`session_id/sequence/actor/event_type/tool/content`）+ `session_manifest.json`（source sha256、adapter、detector 分数、coverage：raw_records/normalized_events/unknown/redactions/skipped、capabilities、warnings）。
- **关键不变量**：逐事件 `provenance`（raw_source/raw_record/raw_sha256/adapter）；脱敏凭据；`verify` 校验 schema 必填、sequence 连续、coverage 一致。
- **进入 mine 前**：先看 manifest 的 `unknown_events`/`redactions`/`adapter_failures`/`capabilities`——确认无异常再继续。

> `--format trace_export|generic|markdown_transcript|claude_code|opencode|codex` 可强制适配器；不确定时保留 auto 与检测分数，不强行套用。Claude/Codex/opencode 的 tool_call 参数（含 file_path/写内容）与 tool_result 载荷均完整保留进事件（供 mine 阶段代码恢复）。

## 阶段 3 · mine（归一化 trace → reconstruction + 候选草稿，LLM，subagent 执行）

主 agent 编排，**执行委派给 subagent**：

1. **相关性预检**：派**门禁子 agent**（`references/subagents/ops-knowledge-trace-relevance-gate.md`）——熟悉 cannbot-skills 的三种 AscendC 算子开发流程（ops-registry-invoke / ops-direct-invoke / ops-direct-invoke-flash），只读 trace 开头 ~60 事件语义判断是否涉及算子生成：`unrelated`（纯问答/闲聊/他领域任务）→ 立即退出（写 `relevance_gate.json` + 最小化 reconstruction/manifest，不产草稿）；`related` → 继续。
2. **挖掘**：派 **`ops-knowledge-trace-miner`** subagent（上下文 = 本条 trace 的归一化事件流 + mining 核心纪律）——重建 `reconstruction.json` → 逐事件扫描（主 trace + 子 agent trace）→ 先枚举修复/诊断/失败/验证四类闭环，再按一根因一形态蒸馏 `DRAFT-*.md` 到暂存目录 → 写 `manifest.json`（candidates + skipped + 每候选的形态化证据合同或 `provenance_missing`）。不得把 `no_validated_after`、`no_full_before_after`、`incomplete_code_chain` 或 `failed_validation` 直接当通用 skip 理由；必须先判断能否转为其他内部 `knowledge_form`。
3. **0 候选合法**：启动片段/纯问答 trace 产出 0 张直接报告；有候选自动接 curate。

对旧批次重挖时，先运行 `scripts/build_rereview_queue.py <旧manifest根> -o <queue.json>`。该脚本只建立可审计队列，不自动接受任何知识。miner 按稳定 shard 逐项完成语义重分类并为新候选重写 manifest/DRAFT，manifest 用 `rereview_decisions[].queue_index` 覆盖每个队列项。完成后运行 `scripts/validate_rereview_output.py <queue.json> <输出根...>`；对单条草稿 curate 也先用 `cluster_candidates.py <草稿目录>` 生成单成员 clusters，不绕过后续 coverage validator。

> **阶段准则（核心纪律 / 输入契约 / 四轨提取 / reconstruction / 证据等级 / 输出 schema）见 [`references/mining.md`](references/mining.md)。** schema 权威 = 本仓 `governance/specs/paths.md` 与 `governance/specs/frontmatter.md`（Runbook Profile），trace 摄入落库契约 = [`references/runbooks-contract.md`](references/runbooks-contract.md)。无 subagent 环境时主 agent 按 mining.md 直接执行（两轨并存）。

## 阶段 4 · curate（草稿 → 门控审查落库，LLM，subagent 执行）

主 agent 编排，**执行委派给 subagent**：

1. **判定与 pending 证据合同**：派 **`ops-knowledge-trace-curator`** subagent（上下文 = 草稿/reconstruction + 现有库 + 定向 normalized evidence slices）——按内部 `knowledge_form` 门控 + 新颖性/去重 → 产出 **ledger.json**（每候选终态 + reason/tier/reproduce_count；`source_drafts` 恰好一次覆盖全部簇成员）。使用同一次调用 `python3 <TRACE_SKILL_DIR>/scripts/materialize_trace_contract.py <mine_dir...> --normalized-root <normalized-root> --ledger <ledger> --clusters <clusters>`：脚本先为每个 mine dir 生成当前 snapshot/reconstruction，再把 snapshot 挂入 ledger；任一 mine dir 失败即整体非零。published/merged 项此时必须保持 `evidence_audit.result: pending`、`verbatim_verified: false`。主 agent 再把所有将新增或修改的最终卡字节写到 ignored 的 `.build/ops-knowledge-trace-ingest/<run>/staged-cards/<area>/<slug>.md`；ledger 的 `target_path` 集合必须与 staged 相对路径集合完全相等。逐 staged 文件运行 `field_notes_lint.py --staged-card <path>`，再运行 `scripts/validate_curated_output.py <clusters.json> <ledger.json> --pre-review`；任何失败都不得进入审查。
2. **独立审查与批准**：对 pending ledger 和 staged cards 先运行 `scripts/validate_review_receipt.py <ledger> <staged-cards> --subject`，再通过 Agent 运行时真正创建**独立** `ops-knowledge-trace-reviewer` subagent（全新上下文，只读），逐字核对机制 artifact、定向 trace 事件和最终卡字节。只接受运行时标明 sender 的原始 subagent 回复；receipt 的 `reviewer` 必须等于该 sender、`attestation` 必须为 `agent-runtime-message`，并带真实 `reviewed_at`。确定性 receipt 校验器只验证字段和字节完整性，**不提供密码学身份认证**；没有可核验 subagent sender 的环境必须 defer，主 agent 不允许自行构造 PASS。blocker/major 清零且 `verdict: PASS` 后，先运行 `validate_review_receipt.py <ledger> <staged-cards> <receipt>`，再以 `materialize_trace_contract.py <mine_dir...> --normalized-root <normalized-root> --ledger <ledger> --clusters <clusters> --verified --receipt <receipt> --cards-root <staged-cards>` 仅把 reviewer-owned approval flags 从 pending/false 改为 pass/true。修改后重新运行 receipt 校验和不带 `--pre-review` 的 `validate_curated_output.py`；v2 subject 会规范化这些 approval flags，其他 ledger 决策或卡片字节变化仍会失效。
3. **主 agent 单一收口**：运行 `python3 <TRACE_SKILL_DIR>/scripts/publish_reviewed_cards.py <ledger> <staged-cards> <receipt> --knowledge-root .`，只把 receipt 绑定的 `<area>/<slug>.md` 原子发布到 Runbook 树；紧接着以相同命令加 `--check` 校验最终目标字节。再运行 `python3 .agents/skills/knowledge-ingest/scripts/knowledge_ingest.py --knowledge-root . sync-indexes` 生成索引，不手写格式；对每张发布卡跑 `field_notes_lint.py --card <path>`，再执行全库门禁。发布后若任一检查失败，禁止直接修知识卡：必须修改 staged card、生成新 subject、重新独立审查和发布。有助于理解结论的跨卡链接在 staged card 中随正文审查，不额外构图。

Curator 先做 active 轨迹证据合同门禁：缺双 SHA/record 锚点、形态化角色、机制 artifact、客观信号、claim mapping 或单点归因的候选保留为 `.build/` support 并 `defer`，不得以复现次数绕过。固定 revision/blob 是优先证据而非轨迹发布的必填项。若 ledger 为零发布，主 agent 不创建空 `knowledge/ops/ascendc/runbooks/` 或 area index；只完成删除后的导航/正文链接与检索索引、coverage、meta/log 与 lint 收口。

双模式：`ingest`（单条/少量）+ `upgrade`（全库复现升级）；批量模式见 §批量模式。

> **阶段准则（双模式 / 门控多锁 / 独立审查 / ledger / 统一收口）见 [`references/curating.md`](references/curating.md)。** 落盘校验跑 `scripts/field_notes_lint.py`（runbooks-contract §6 HARD 约束）。

## 批量模式（千级 trace：`parsed/context/**` 批量摄入）

输入为含大量 `ses_*.md` 的目录时走批量流水线（设计细节见 [`references/batch-scaling-and-subagents.md`](references/batch-scaling-and-subagents.md)）：

```
目录(千级 md)
  ├─① trace_normalize.py batch <目录>        # 0 LLM，多进程，幂等（batch_manifest.json）
  ├─② 门禁扇出：门禁 subagent 批处理（5~10 条/调用，gates.json）→ 只对 related 继续
  ├─③ mine 扇出：每 related trace 派 miner subagent，主 agent 并发 N 个（默认 4~8，可配）
  │      batch_manifest 记状态（normalized/gated/mined/failed），断点续跑
  ├─④ 预聚类：scripts/cluster_candidates.py <全部草稿目录> -o clusters.json   # 0 LLM
  │      簇 = 同根因跨 trace 聚合；簇内 cross_trace 数 → 复现判定批量来源
  ├─⑤ curate 聚合：分域派 curator subagent（簇级门控 + 对库近邻去重）→ 各域 pending ledger
  ├─⑥ 主 agent 生成 staged cards → reviewer 独立审查（新增主卡 + 升级/合并操作）→ receipt 批准
  └─⑦ 主 agent 单一收口：原字节发布 → sync indexes → lint + query → log + meta
```

- 并行度只受环境并发 task 上限约束；token 预算充足，无预算分批（质量优先）。
- 用户明确要求从 batch 阶段重启时，复用 `batch_manifest.json` 状态实现幂等/断点续跑；不要把阶段名当成脚本参数。

> **试点限定**：批量流水线的门禁扇出/并发编排尚未经千级试点，执行时以 [`references/batch-scaling-and-subagents.md`](references/batch-scaling-and-subagents.md) 为设计参考，先跑小样本回归再放量。

## 全量重建模式（rebuild）

只在用户明确要求“清空当前 runbooks，再从完整轨迹重建”时执行：

1. 删除前固化旧卡数、Git commit/工作区、原始输入 inventory（主会话/子 agent/字节数），并运行全库 `knowledge_lint.py --strict-navigation`和检索索引 full verify 记录基线；先用一条 related 和一条 unrelated 轨迹回归 adapter/verify/门禁。
2. 在 Git 可恢复的前提下整树删除 `knowledge/ops/ascendc/runbooks/`，同步移除 `knowledge/ops/ascendc/index.md` 中的直接 Runbooks 导航；`knowledge/index.md` 只列 domain，不修改。同步清理其他卡片指向已删除卡片的普通链接；本地图谱是按需派生产物，不参与此次收尾。
3. 新一轮 mine/cluster/curate 以**空库**为准，不读取、拷贝或对齐 Git 历史中的旧卡，不继承旧 slug/文本/复现计数；跨轨迹复现只按本轮不同 source SHA-256 计数。
4. reviewer 通过后由主 agent 单一收口：有 approved active 卡时才重建 area 目录与逐层 index、恢复 `knowledge/ops/ascendc/index.md` 的 Runbooks 导航；若零发布则保持 runbooks 整树不存在且 AscendC 入口无该导航。两种结果都维护可解析的正文链接，重建检索索引、写 rebuild ledger/meta/log，最后跑 field_notes_lint 与 knowledge-lint。

## 输入契约

- **parse**：单个 `session=ses_*/` 目录（直接传，自动识别）或含多个 `session=ses_*/` 的父目录（外部仓 `~/cannbot-gateway-log*` 会话日志形态）。
- **normalize**：parse 产出的 trace 目录，或任意轨迹导出（JSON/JSONL/文本/zip/tar/目录），或 算子开发会话 `parsed/context/ses_*.md` 转写（单文件/目录），或**主流 agent 框架日志**——Claude Code `~/.claude/projects/**/*.jsonl`、opencode session JSON、Codex `~/.codex/sessions/<date>/*.jsonl`（专项适配器；opencode 适配器目前经合成 fixture 验证，真实导出建议先 `detect` 核对 adapter 与 coverage 再 full-run）；远程来源先物化为本地文件。
- **batch**：含大量 `ses_*.md` 的目录（如 `parsed/context/` 或其子目录）→ 批量流水线（§批量模式）。
- **mine**：normalize 产出目录（`normalized_trace.jsonl` + `session_manifest.json`）。兼容旧输入（`trace_skeleton.json` + `trace.json`）。
- **curate**：mine 暂存草稿目录 或 `upgrade`（扫 `knowledge/ops/ascendc/runbooks/` 全库）。
- **全流程**：给日志目录 / 转写 / 轨迹导出 → parse|normalize→mine→curate 串行**一气呵成**（默认行为，见 §阶段切换）；仅当用户指名单阶段时停在中间。

## 输出

- parse：`<out>/trace_<ses>/{trace.json,trace.md,tree.txt,summary.json,attachments/,subagents/}`。
- normalize：`<build>/trace-normalized/<sha12>/{normalized_trace.jsonl,session_manifest.json}`（脱敏后、带 provenance）。
- batch：`<build>/batch-<日期>/trace-normalized/<sha12>/...` + `batch_manifest.json`（每源文件状态：ok/skipped/error）。
- mine：`.build/ops-knowledge-trace-ingest/<日期>/<trace_id>/{relevance_gate.json(预检退出时),manifest.json,reconstruction.json,DRAFT-<area>-<n>.md}`（gitignored）。
- curate：`knowledge/ops/ascendc/runbooks/<area>/<slug>.md`（新建/增量合并/升级）+ index 刷新 + ledger 终态 + `logs/<日期>.md` 条目；跨卡引用使用普通 Markdown 链接。
- **预检退出**（unrelated）：只产出 `relevance_gate.json` + 最小化 `reconstruction.json`/`manifest.json`，不产 DRAFT、不落库，全流程直接以报告收尾。

## 职责边界（与 Ingest / Query / Lint 的分工）

- **本 skill** → `knowledge/ops/ascendc/runbooks/<area>/`（现象/任务驱动卡：精度/工程/性能/完整配方 × compilation/runtime/precision/performance/validations；area 由 curate 阶段按内容判定）。
- `knowledge-ingest` 负责官方文档/固定源码的静态摄入与按需链接图谱；本 skill 只负责 trace → runbooks 的动态摄入，并由 Ingest 路由 trace 来源到本仓内 producer。
- `knowledge-query` 消费 runbook 卡（`type: Runbook`，按 Runbook Profile 统一归一）；`knowledge-lint` 通过统一 Contract 校验 `runbooks` Profile 的机器约束。
- 不同知识产物，不混用目录。

## 收尾校验

证据角色、artifact 类型、重建方式和连续 sequence 校验由 `scripts/validate_curated_output.py` 统一提供；相关物化与复审工具直接复用。文件 SHA-256 由 `scripts/validate_review_receipt.py` 统一计算，发布目录范围从仓库 Contract 获取。

1. review 前对每张 staged card 跑 `python3 <SKILL_DIR>/scripts/field_notes_lint.py --staged-card <path>`；发布并完成 `publish_reviewed_cards.py --check` 后，再对每张目标卡跑 `--card <repo-relative-path>`，最后无参数运行一次 AscendC Runbook 全库兼容检查，三者 HARD 都为 0。任何发布后修订都必须回到 staging 并重新审查。
2. `knowledge/ops/ascendc/runbooks/<area>/index.md` 只列本层直接卡。普通正文链接由统一 Contract 校验，不要求额外关系块或图谱缓存。
3. **反投机取巧抽检**：无卡把放宽容差/改测试/改期望当解决配方（正知识）；`## 验证信号` 无"前序 LOG.md/本 trace 未复现"字样。
4. **形态化证据抽检**：逐卡核对内部 `knowledge_form`（manifest/ledger）与对应角色合同；核心机制 artifact 正文内联并与事件流逐字一致。只有 `repair_recipe` 强制完整 before/after。
4a. **active 轨迹证据合同抽检**：`trace_snapshot` 逐卡核对实际 normalized 路径、raw/normalized 两个完整 SHA-256、sequence/coverage、形态化角色锚点和 artifact 重建方式；`fixed_source` 逐卡核对 40 位 revision 与精确 blob 导航。
5. **价值抽检**：无低价值/常识性/纯流程类卡落库（对照 mine `skipped` 清单与 runbooks-contract §0 判据）。
6. **适用性与路线抽检**：抽查新落库卡含 `## 适用场景`（工程形态/API 路径/验证平台与版本/适用粒度/路线优先级/不适用场景）（约束㉑）；`safety_fallback` 卡含 fallback 声明；`platforms` 只含实际验证平台（推断平台在 `## 失效边界` 标注“未验证，推断可迁移”）；`## 验证信号` 逐条标来源平台+证据等级；无绝对单跑分数落正文（相对代价须成对标注参照路线）；同问题域冲突或方案选用条件已在正文说明，必要时链接对应卡片。
7. **图谱按需**：日常入库不运行图谱命令，不做全库关系判定；仅在需要查看卡片链接时使用 knowledge-ingest 的 [本地图谱](../knowledge-ingest/references/local-graphs.md)。

8. **预检退出校验**：unrelated 退出时暂存目录含 `relevance_gate.json` + `manifest.json`（candidates=[]、skipped 记 `not_ascendc_related`），无 DRAFT、无知识卡目录改动。
9. 写 `logs/<YYYY-MM-DD>.md` 条目（本仓规范，时间取 `date`）。
10. 运行全库 [`knowledge-lint`](../knowledge-lint/SKILL.md)、检索索引 full verify、目标 Query 和根 `bash check.sh`；索引必须与当前知识一致。

## 完成报告

每轮 ingest 结束时向用户报告：输入来源与 adapter、归一化 coverage、相关性预检、重建能力、价值筛除统计、机制 artifact 恢复情况、捷径检出、候选与终态；**必须同时按内部 `knowledge_form` 报告 mined/published/deferred 数量**（此分类只用于内部对账，不落卡 frontmatter），并列出旧式 `no_validated_after`/`incomplete_code_chain` skip 中被重新分类和仍 defer 的数量，防止用总卡数掩盖某类知识被系统性漏挖。仅在按需构图时报告其结果。

## 设计借鉴

- 输出 schema / 目录 / validator → 本仓 `governance/specs/paths.md` + `governance/specs/frontmatter.md`（Runbook Profile：`type: "Runbook"`，必填 `platforms`，trace 摄入 `sources` 可空 `[]`）+ [`references/runbooks-contract.md`](references/runbooks-contract.md)（正文章节、验证信号、失效边界与证据合同；frontmatter 不设 evidence/confidence/transfer_scope/quality_score/reproduce_count，溯源见正文 `## 验证信号` 段首来源说明）。
- 确定性规范化 / 溯源 / 脱敏 / coverage / verify → 源自 `ops-knowledge-trajectory-ingest` 的 `trajectory_ingest.py` 设计，落地为 `scripts/trace_normalize.py`。
- parse 算法 → 原 `cannbot-log-parser`（已并入 `scripts/parse.py`）。
- mine/curate 准则 → [`references/mining.md`](references/mining.md) / [`references/curating.md`](references/curating.md)（源自原 trace-miner/curator，已从 field-notes 体系迁移到 runbooks 落库契约）。
