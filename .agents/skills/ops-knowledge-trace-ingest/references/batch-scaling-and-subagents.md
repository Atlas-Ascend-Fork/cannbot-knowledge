# 规划：trace-ingest 大规模批量处理与 miner/curator subagent 化

> 本文为批量模式的设计与实现现状（⏳ 项为未试点限制，不代表 CLI 缺失）。
> 背景：`parsed/context/` 下可能有上千条会话 md；当前 skill 为单 trace 串行流水线（normalize → mine → curate，主 agent 全流程），无法直接应对。
> **前提：token 预算充足（用户声明），设计以质量为优先，不做成本压缩**——省 token 不是设计目标；门禁/预聚类/单一收口等结构保留是因为它们是质量、一致性与可审计性需求，不是因为成本。

## 实现状态（2026-08-07）

| 项 | 状态 | 落点 |
|----|------|------|
| miner subagent | ✅ 已实现 + 单条回归（8 草稿/9 skipped） | `subagents/ops-knowledge-trace-miner.md` |
| curator subagent | ✅ 已实现 + 单条回归（ledger：covered/defer 判定合理） | `subagents/ops-knowledge-trace-curator.md` |
| reviewer subagent | ✅ 已实现（只读，审新增主卡+升级操作） | `subagents/ops-knowledge-trace-reviewer.md` |
| 批量 normalize | ✅ 已实现（多进程/幂等/batch_manifest） | `trace_normalize.py batch` |
| 草稿预聚类 | ✅ 已实现（跨 trace 并簇验证 14→7） | `scripts/cluster_candidates.py` |
| SKILL.md 阶段 3/4 subagent 化 + 批量模式文档 | ✅ 已同步 | `SKILL.md` |
| 批量扇出实际执行（门禁批处理/并发 N/分域 curator） | ⏳ 待批量试点验证 | 主 agent 编排行为，按 §2 执行 |
| 千级试点 | ⏳ 待执行 | — |



## 1. 问题与现状

| 现状 | 瓶颈 |
|------|------|
| normalize 0 LLM，单输入 | 已实现 `batch` 子命令（多进程/幂等）；千级扇出编排待试点 |
| mine 主 agent 逐事件扫描（LLM 重） | 千级串行不现实；主 agent 单上下文无法容纳 |
| curate 主 agent 落库 + 对库去重 | 库级操作天然全局，不能按 trace 并行写 |
| 主 agent 同时做编排与执行 | 上下文膨胀、无法并发 |

## 2. 总体架构：三层扇出-聚合（Batch Pipeline）

```
parsed/context/**/*.md（千级）
   │
   ▼ ① 批量 normalize（0 LLM，多进程脚本）
.build/batch-<date>/trace-normalized/<sha12>/{normalized_trace.jsonl, session_manifest.json}
   │  + batch_manifest.json（源文件/sha256/事件数/adapter/状态）
   │
   ▼ ② 门禁预检扇出（LLM 轻量：每 trace 只读开头 ~60 事件；每 subagent 批 5~10 条）
.build/batch-<date>/gates.json        # trace_id → {verdict, confidence, reason}
   │  只对 related 继续（unrelated 标记跳过，不进 mine）
   ▼ ③ mine 扇出（LLM 重：每 related trace 一个 miner subagent，并行 N）
.build/ops-knowledge-trace-ingest/<date>/<trace_id>/{reconstruction.json, manifest.json, DRAFT-*.md}
   │
   ▼ ④ curate 聚合（LLM：全局去重 + 落库；分域并行 + 统一收口）
knowledge/ops/ascendc/runbooks/** + batch ledger + 图谱增量（含 judge，必做） + log
```

### ① 批量 normalize（0 LLM）
- `trace_normalize.py` 增加 `batch <目录>` 子命令：扫描目录下全部 `*.md`，`multiprocessing` 并行（默认 `os.cpu_count()`），逐条 normalize 到 `.build/batch-<date>/trace-normalized/<sha12>/`。
- 幂等：目标目录已存在 → 跳过（断点续跑的基础）。千级分钟级完成。
- 产出 `batch_manifest.json`：`[{src, sha256, events, adapter, status, error?}]`。

### ② 门禁预检扇出（质量过滤，非成本手段）
- 复用 `subagents/ops-knowledge-trace-relevance-gate.md`（只读开头 60 事件）。
- 门禁保留的动机是**知识库纯度**：无关会话（纯问答/闲聊/他领域）不进入挖掘与落库，避免噪声知识污染库；不是为省 token。
- **批处理化**：每个门禁 subagent 一次处理 5~10 条 trace（每条只读开头），批量输出 verdict 列表——减少并发调度开销（并发受限时提升吞吐）。
- 产出 `.build/batch-<date>/gates.json`；unrelated 率可统计（供人工了解输入构成，非止损开关）。
- 门禁可顺带输出每条 related trace 的一句话主题（算子名/流程类型），用于产出物分组与审计。

### ③ mine 扇出（并行核心）
- 每个 related trace 派 `ops-knowledge-trace-miner` subagent（§3），**主 agent 一次并发派 N 个**（N 默认 4~8，受环境并发 task 上限约束，可配置）。
- 每 subagent 上下文 = 一条 trace（事件流按需读）+ mining 核心纪律；产出到各自暂存目录。
- `batch_manifest.json` 记录每 trace 状态（`gated/related/mined/failed`）；失败重试、已完成跳过（断点续跑）。
- **并行策略（token 不限）**：全部 related trace 持续排队并行处理（不受预算分批约束）；按算子/主题分组可选（便于审计与产出物组织），非成本要求。

### ④ curate 聚合（深度设计：缩维 → 簇级判定 → 单一收口）

**Curator 的瓶颈不是 LLM 判定，而是比对规模**：N 草稿 × M 库卡的全比对（500×100=5 万对）LLM 无法处理。必须先**确定性缩维**，再在近邻对上做语义判定。同时门控语义从"逐卡"升级为"簇级"。

```
全部 mine 产物（DRAFT-*.md + manifest.json + reconstruction.json）
   │
   ▼ ④a 确定性预聚类（0 LLM 脚本 cluster_candidates.py）
   .build/batch-<date>/clusters.json
   每簇 = {members, 特征(phenomenon+solution_layer+signal词+根因句), trace_ids, 跨trace数}
   │
   ▼ ④b 库侧特征化 + 近邻检索（0 LLM，库特征可缓存）
   每簇取 Top-K（5~10）语义近邻库卡 → 比对对清单
   │
   ▼ ④c 簇级门控与去重判定（LLM，curator subagent 分域并行）
   每簇：主卡选择 → 跨trace复现计数 → 对近邻库卡判定
     new / upvote(主卡 reproduce_count+=n) / merge(补字段) / covered / reject
   门控锁在簇主卡判（价值/防作弊/代码完整/验证信号）；成员卡只做确定性检查
   → 每域 ledger.json（.build/，不直接写库）
   │
   ▼ ④d 独立审查（reviewer subagent，只读）
   审"新增主卡最终稿 + 升级/合并操作"（不逐卡审草稿）
   │
   ▼ ④e 主 agent 单一收口（唯一写者）
   ledger 合并 → 落盘新增/合并/升级 → index → 图谱 judge/inject（含双向反链） → log + meta
```

**④a 确定性预聚类（必须 0 LLM）**
- 特征：`type + phenomenon + solution_layer + signal 共享词 + 根因句字符 n-gram`；
- 贪心聚类（相似度阈值并簇）；产出簇清单含**跨 trace 数**（这是批量 `reproduce_count` 的来源）；
- 细粒度已由 mine 保证（每候选一根因一知识形态），簇 = “同 knowledge_form + 同根因跨 trace/跨候选”聚合；不同形态不得自动聚为一个证据合同；
- 预聚类保留的动机是**判定一致性与可审计性**（同根因候选一次判定、一次计数），不是省 token；漏并后果轻（同 nugget 落两次 → 下次 upgrade 合并），误并由 ④c 判定时拆出。

**④b 库侧近邻（一致性而非成本）**
- 库卡同样特征化（可缓存 `.build/`），每簇检索 Top-K 近邻 → 判定对从 N×M 全比对收敛到 簇数×K；
- 收敛的动机是**让同 nugget 判定可复现、可审计**（每簇固定近邻窗口），兼带避免全比对噪声。

**④c 簇级门控与去重（LLM）**
- 簇主卡 = 证据最全/代码最完整者；门控锁（实测锚定/防作弊/价值/代码完整/验证信号禁 hearsay）在**主卡**判；
- **批量天然含 upgrade 语义**：簇内跨 trace 复现 ≥2 且主卡上板信号 `tool_observed`/`artifact_verified` → 一次落库直接 `verified`（不放松双门槛，逐簇过证据锁）；
- 对近邻库卡：同 nugget → upvote/merge；同现象不同根因 → 写图谱关系候选，不手写反链；
- reject/defer 成员（低价值/作弊/证据不足）记 ledger reason，供用户人工复审。

**④d 审查按簇不按卡**
- reviewer 只读：新增主卡最终稿 + 簇判定记录 + ledger；UPVOTE/合并等低风险操作不逐条审；
- 审查成本 = O(新卡数)，不是 O(草稿数)。

**④e 单一收口（写库唯一入口）**
- 分域 curator 只产出 ledger，**不直接写知识卡目录**；index 由主 agent 串行落盘，反链由后续 graph inject 统一写入；
- 图谱增量一次（必做，非条件式）：新增卡批量 judge（一个 judge 子 agent 判全部新 focal，覆盖新卡的跨树候选：knowledge 其他树邻居）→ aggregate → inject/viz/verify；runbooks 与 knowledge 其他树的跨树链接由图谱 pipeline 产生、不手写（手写反链与 inject 幂等冲突）。

**规模参考（500 草稿示例）**：④a/b 确定性秒级；④c ~100-200 簇 × 每簇 5~10 近邻对 ≈ 1000-2000 对语义判定（分域 curator 并行）；④d ~50-100 新主卡。curator 判定量级约为 mine 的 1/50——**token 不限，但判定对规模收敛仍保证同 nugget 判定一致可审计**。

### 规模与并行策略（token 不限）
- 并行度只受环境并发 task 上限约束；全部 related trace 持续排队处理，无需预算分批。
- 断点续跑（batch_manifest 状态机）保证任意中断后可恢复，不受规模影响。
- 可选按算子/主题分组组织产出物（审计友好），非成本要求。

## 3. miner / curator / reviewer subagent 化

### 动机
- **上下文隔离**：mine 子 agent 只持一条 trace；curate 子 agent 只持草稿+库（天然满足"不读 trace 长文"纪律）；reviewer 全新上下文（天然满足独立审查）。
- **并行**：mine 每 trace 独立 → 扇出并行；curate 分域并行。
- **纪律硬隔离**：subagent 定义硬性限制 read 范围与写权限，替代"reference 文档靠自觉"。
- 与既有先例一致：`relevance-gate` subagent（已实现）、曾删除的 code-comparator。

### 三个新 subagent

**A. `subagents/ops-knowledge-trace-miner.md`（mine 执行者）**
- 输入：trace 暂存目录路径（normalize 产物 + 门禁 verdict）+ 暂存输出路径。
- 权限：read/glob/bash（读事件流）；**write 仅限 .build 暂存**；**禁读 knowledge/ops/ascendc/runbooks**（防锚定）；禁 edit 库文件。
- 职责（内联 mining.md 核心纪律 + 引用细则）：reconstruction → 逐事件扫描四种 knowledge_form → 价值预筛 → DRAFT 草稿（形态化机制证据 / 反投机取巧 / 证据等级）→ manifest（candidates + skipped + skipped 重分类对账）。
- 输出：结构化确认 `{candidate_count, skipped, manifest_path}`。

**B. `subagents/ops-knowledge-trace-curator.md`（curate 判定者，产出 ledger）**
- 输入：`clusters.json`（④a 预聚类）+ 库特征索引（④b）+ 近邻比对对清单 + 现有库根。
- 权限：read/glob/bash + **write 仅限 `.build/`**（写 ledger）；**禁读 trace 长文**；**不直接写知识卡目录**（写库由主 agent 收口）。
- 职责（按簇级门控，见 §2.④c）：簇主卡选择 → 跨 trace 复现计数（reproduce_count / 批量 upgrade 语义）→ 对近邻库卡判 new/upvote/merge/covered/reject → 门控锁在簇主卡判。
- 输出：分域 `ledger.json`（每簇终态 + reason + 主卡/合并字段/相关反链建议）。

**C. `subagents/ops-knowledge-trace-reviewer.md`（独立审查，按簇不按卡）**
- 输入：新增主卡最终稿 + 簇判定记录 + ledger + SPEC 摘要（不给 trace、不给草稿全量）。
- 权限：**read only**（edit/write deny）。
- 职责：对照 curating.md blocker 清单输出 `{blocker|major|minor}` findings（含：无实测信号 / agent_reported 当实测 / 测试侧放松 / 低价值发布 / hearsay 验证信号 / 代码不完整）；UPVOTE/合并等低风险操作不逐条审，只审新增主卡与升级操作。
- 输出：`findings.json`；修订后重审，blocker+major 清零才放行。

### 主 agent 角色变化
- 单条模式：main → 门禁 subagent → miner subagent → reviewer subagent → curator subagent → 收口（图谱/索引/log）。
- 批量模式：main → 批量 normalize（脚本）→ 门禁扇出 → mine 扇出（并行 N）→ 预聚类（脚本）→ curator（分域并行，产出 ledger）→ reviewer（审新主卡）→ **main 单一收口落库** → 图谱增量（含 judge，必做） → log。
- 主 agent 上下文只装：batch manifest、gates.json、clusters.json、各 subagent 结构化返回、各域 ledger。

### 与 reference 文档的关系
- `reference/mining.md` / `reference/curating.md` 保留为**准则权威**（详细判据/词表/示例）。
- subagent 定义内联**核心纪律**（一卡一根因、价值门槛、反投机取巧、代码 verbatim、证据等级、不落库、门控锁、blocker 清单），细则按需读 reference。
- 兼容：无 subagent 环境时主 agent 仍可按 reference 直接执行（两轨并存，subagent 优先）。

## 4. 落地路线（建议实现顺序）

| 阶段 | 内容 | 验证 |
|------|------|------|
| 1 | miner/curator/reviewer 三个 subagent 定义 + SKILL.md 阶段 3/4 改派 subagent | 单条模式回归：用 ses_0a09e092 重跑，对比产出与成本 |
| 2 | `trace_normalize.py batch` 多进程 + batch_manifest + 门禁批处理（5~10 条/调用） | parsed/context/ascendc/ 全量门禁，统计 unrelated 率 |
| 3 | mine 扇出并发（N 配置化）+ 断点续跑 + 成本护栏；curate 聚合去重 + 分域并行 + 统一收口 | ascendc/ 335 条批量摄入，评估产出率与 token 成本 |
| 4 | 全量 parsed/context/（千级）试点 + 分批策略调优 | 产出率/成本报告 |

## 5. 风险与对策
- **并行写库冲突**：curate 库写入由主 agent 单一收口，分域 subagent 只产出 ledger，不直接写库；反链由后续 graph inject 单点写入。
- **subagent 写权限失控**：write 权限限定 `.build/`（curator 写 ledger）；落库写权限只在主 agent；reviewer 零写权限。
- **并发稳定性**：海量并行受环境并发 task 上限与 API 限流约束——batch_manifest 状态机 + 失败重试 + 断点续跑保证可恢复；限流时降低并发 N。
- **预聚类误并/漏并**：簇清单可抽查；漏并后果轻（同 nugget 落两次 → 下次 upgrade 合并）；误并在簇级判定时拆出。
- **批量 verified 升级过松**：跨 trace 复现 + 上板信号双门槛不放松，逐簇过证据锁后才升 verified。
- **质量退化**：每批 curate 后抽查（lint HARD=0 + 价值抽检 + 簇判定抽检），对照单条模式基线。
