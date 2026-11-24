---
type: Optimization
title: 向量核串行 scan 链两阶段改造（屏障强度按 dtype 分裂降级 → 串行链改对数深度树扫描）
description: 串行 scan 链两阶段改造：链内屏障按输出 dtype 降级（低精度 PIPE_V、高精度保留 PIPE_ALL）；串行链改对数树扫描，每波单屏障、ping/pong 双缓冲。
tags:
- task.optimization
- topic.programming_model.execution_unit.cube
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/cv-A5/31-scan-chain-barrier-downgrade-and-log-tree-scan.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：向量核串行 scan 链两阶段改造（屏障强度按 dtype 分裂降级 → 串行链改对数深度树扫描）

> **来源：A5 自由探索实测（sequential_linear_cumsum__v2，2026-09-12，device 4）**
> direction_key（阶段一）: `aiv-vec::kahan-scan-pipe-all-to-pipe-v-barrier-downgrade::scan-loop`
> direction_key（阶段二）: `aiv-vec::serial-kahan-scan-to-log-depth-tree-scan::scan-loop`
> 证据（阶段一）：<AOA_ROOT>/AOA/AOA_skill_run_v2/aoa_out/sequential_linear_cumsum__v2/loop_<run-id>/explore/direction_001/evidence_run/final/bench_paired_3pairs.log
>       （A=冻结基线 .so `_C_base_0911_1755.so`，B=阶段一改造后 .so，3 对平衡交替，23 case，B_over_A_geomean=0.374727）
> 证据（阶段二）：<AOA_ROOT>/AOA/AOA_skill_run_v2/aoa_out/sequential_linear_cumsum__v2/loop_<run-id>/explore/direction_002/evidence_run/final/bench_paired.log
>       （A=同一冻结基线 .so `_C_base_0911_1755.so`，B=在阶段一 champion 之上叠加树扫描的 .so，3 对平衡交替 (A,B/B,A/A,B)，23 case，B_over_A_geomean=0.202911）
> 实测：阶段一 2.6686 x（相对冻结基线重建 .so；fp16/bf16 16 case 2.67x~4.87x 同向加速，fp32 7 case ±0.16% 持平）；两阶段累计 4.9283 x（相对同一冻结基线；23/23 case 同向加速无回退，逐对离散 0.09% << 0.5% 噪声门）。**4.9283 x 是两阶段累计增益，不是树扫描的独立增益**；阶段二相对阶段一的增量按两组配对值相除推得 4.9283/2.6686≈1.85 x（推算值，非独立测量）。精度均 PASS（23/23；阶段一与基线逐位一致，阶段二 fp32 7 case bad_ratio=0，树扫描数值性优于 Kahan 形态），改动前 bad_ratio 情况如证据所述（基线 Kahan 链 23/23 PASS）。

## 原理

向量核上的逐行串行 scan（如 cumsum 前缀和）链，典型形态是「行 r 依赖行 r-1 的累计值」：每行若干条向量指令、每条指令后一次屏障，行数 × 指令数 × 屏障次数全部落在关键路径上（实测形态：每 tile 128 行 × 5 指令 + 5 屏障 = 最多 640 条屏障 + 640 步串行依赖，树高 O(validM)）。两个正交维度先后削减：

**阶段一（屏障强度维度）**：精度修复期保守取最强屏障（PIPE_ALL，排空全部流水）逐条锁定链内依赖。但链内相邻指令的读写集全在 UB 内、同为 Vector 指令——依赖边只需约束 V 流水内部顺序（PIPE_V），PIPE_ALL 属过度保守。按输出 dtype 编译期分裂屏障强度：低精度输出（fp16/bf16）链内降为 PIPE_V（V→V 读写依赖边 PIPE_V 充分，16 case 与基线逐位一致实证）；高精度输出（fp32）**保留逐行 PIPE_ALL**——其实测形态（链内 PIPE_V + 收尾补条 PIPE_ALL）精度虽过，但在 profiling 采集包裹下出现 aicore timeout 挂死且无性能收益，回到与基线逐指令一致的最强形态以消除行为漂移与可采集性风险。

**阶段二（依赖链深度维度）**：把串行 scan 改为对数深度 inclusive 树扫描（Hillis-Steele）：波 d∈{1,2,4,...}，波内「行 r += 行 r-d」全部互不依赖，每波只需一次屏障；关键路径从 5×validM 步降到 ceil(log2(validM))+2 波、屏障从 640/tile 降到 ≤9/tile。要点：
- **种子/进位语义**：跨 tile 的 carry = 上一 tile 末行的 inclusive 前缀和，融入下一 tile 首行（seed += carry），与原 running seed 延续语义等价；每模块首 tile 种子清零。
- **ping/pong 双缓冲**：波间读写交替使用两块 UB 缓冲，消除波内 V→V 读写冲突；UB 预算重算（实测形态：原缓冲 + 新增第二缓冲 ≈ 113.5KB < 192KB 上限，同时删除补偿链临时缓冲）。
- **扁平宽波形态**：行距==列数（tile 在 UB 内连续）时每波塌缩为 2 条整 tile 宽向量指令（前 d 行终态续拷 + 错位相加），每 tile 指令数 ~2·log2(M)+2。**逐行窄指令形态（~M·log2(M) 条）实测失败**：发射开销（实测地板 ~12ns/条）反超原串行链，必须用宽波。
- **屏障强度沿用阶段一结论**：低精度输出波间 PIPE_V；高精度输出（fp32 直通 MTE3 写路径）保守逐波 PIPE_ALL——即使保留最强屏障，屏障计数从 640 降到 7 仍显著收益（fp32 case 从阶段一的平台期进入 2.7x~4.5x 改善域）。
- **数值性**：树扫描改变浮点结合顺序，每输出误差 O(log M·eps·Σ|h|)，优于朴素逐行累加的 O(sqrt(L)·eps)、介于朴素与补偿链之间；实测 fp32 7 case bad_ratio=0（优于 Kahan 形态），低精度输出下舍入不可观测。

## 性能问题模式（哪些 profiling 信号说明该用）

- msOpProf PipeUtilization：aiv_vec 为 top1 流水（实测 champion 阶段 fp16 79.9% / bf16 84.7% / fp32 59.3%），aiv_scalar 叠加 61~85%，矩阵计算 pipe 除个别 dtype 外 <7%。
- 代码指纹：scan/递推段「每行 N 条指令 × 每条后跟屏障」的串行链；屏障强度是全流水级（PIPE_ALL）而读写集全在 UB 的 V→V 依赖。
- dtype 分桶信号：低精度输出 case 改屏障强度即收益、高精度 case 持平（其屏障本就保守）——提示两个维度分别施策。
- 无依赖段的屏障塌缩/批量化策略（收尾段合并类）收益已饱和后，有依赖链的 scan 段仍是向量核时长主体。
- 收尾 cast/写回已整块化后，每 tile 指令数与屏障数仍被 scan 段锁死在 O(行数)。

## 正确性红线（什么情况下禁止用 / 必须回退）

1. **V→V 依赖边 PIPE_V 充分性须实证**：降级屏障强度前，确认该依赖边读写集全在 UB、无跨流水（MTE/Fix）参与；写侧经队列框架同步（TQue EnQue/DeQue）+ 写回后全流水屏障兜底。任何跨流水可见性需求（如 fp32 直通写 GM 路径）保留 PIPE_ALL——弱屏障形态曾致 profiling 采集下 aicore timeout 挂死，且该形态无收益即回退。
2. **树扫描改变结合顺序**：输出误差从 O(eps) 级补偿精度变为 O(log M·eps·Σ|h|)；高精度输出 dtype 必须以全量精度用例实测 bad_ratio 兜底（本例 fp32 bad_ratio=0 通过；不通过的 dtype 保留原串行补偿链）。
3. **种子/进位不能丢**：跨 tile carry 融入首行、每模块首 tile 种子清零、末行 inclusive 前缀写出——三处任一遗漏即功能错误（少加/重置脏值）。
4. **ping/pong 缓冲不可省**：波内同缓冲读写会竞态；UB 预算含第二缓冲后须仍在上限内（双槽队列缓冲叠加时按最坏组合重算）。
5. **禁止逐行窄指令树形**：每行单独发射窄向量的树扫描指令数 ~M·log2(M)，发射开销反超收益（实测回退）；行距==列数才走扁平宽波，padded 形态保留防御性逐行波形并验证。
6. **dtype 分支编译期隔离**：`if constexpr` 类机制，保证未改路径逐指令不变（零扰动）。
7. **累加域 dtype 与输出 dtype 分离论证**：低精度输出走弱屏障/树扫描的精度论证前提是「累加域每步舍入 << 输出量化步长」（见 `30-dtype-adaptive-naive-scan` 红线 2），论证不成立时全 dtype 保守。

## 泛化条件（dtype / shape / 流水线 / 算子类型）

- 流水线：aiv_vec（向量计算+同步主导），屏障/标量开销显著时 aiv_scalar 同受益。
- 算子类型：任何「逐行串行依赖的向量 scan/递推（前缀和、累积量、递推链）」路径，列间独立可分；不限具体算子。
- shape：tile 行数多（链长）收益最大（关键路径 O(M)→O(log M)）；行距==列数的连续 tile 可走扁平宽波（指令数最省）。
- dtype：低精度输出可用弱屏障+树扫描；高精度输出树扫描须精度实测兜底、屏障保守逐波最强。
- 两阶段可独立施策：只降屏障强度（保留串行链）对低精度输出即有收益；树扫描含屏障策略（波间单屏障），叠加后收益最大。与 tiling、搬运类策略正交。
- 与 `10-reduction-tree-fixedpoint`（逐行归约存树 + 定点事件同步）的区别：本条改造 **scan 段内的行间依赖链**（前缀依赖，输出每行都是部分和）；10 处理**块间归约结果的树形合并**（max/sum 归约，块间无前缀依赖），二者作用域不同、不重复。

## 实施步骤（从证据里的真实 diff 抽象成通用步骤）

1. 量化 scan 段成本：每行指令数 × 每行屏障次数 × 行数/tile；profiling 确认 aiv_vec 为 top1、scan 段是其中时长主体。
2. **阶段一**：按输出 dtype 编译期分裂链内屏障强度——低精度输出降为 V 流水级屏障，高精度输出保留全流水级逐条不变；全量精度用例 + 逐位一致性验证，并用 profiling 包裹采集复测（无挂死、无行为漂移）。
3. **阶段二**：把串行链改写为对数深度树扫描——种子融入首行、波倍增错位相加、ping/pong 双缓冲、每波单屏障、末行前缀作 carry-out。
4. 行距==列数时实现扁平宽波（每波 2 条整 tile 宽指令：终态续拷 + 错位相加）；padded 形态保留逐行波形分支。
5. UB 预算重算（新增第二缓冲、删除补偿临时缓冲），超限则回退串行链。
6. 全量精度用例过门（重点：高精度输出 dtype 的 bad_ratio、种子/进位边界、首 tile 与尾 tile）；3 对平衡交替配对复测（A 侧写明冻结基线身份），确认逐对离散 << 噪声门。

## LLM 前置问题（应用前必须自问）

1. scan 段每 tile 的指令数与屏障数各是多少？屏障强度是全流水级还是 V 流水级？读写集是否全在 UB 内？
2. 各输出 dtype 的精度 tol 与量化步长差多少量级？哪些 dtype 允许弱屏障/结合顺序变化、哪些必须逐指令保守？
3. 树扫描的误差界 O(log M·eps·Σ|h|) 相对该算子精度判据是否可接受？有无相消敏感 case？
4. 种子/进位三处（首 tile 清零、跨 tile 融入、末行 carry-out）如何表达？padded 行距走哪个分支？
5. UB 预算加第二缓冲后是否仍在上限内？与已有双缓冲/队列槽位叠加后最坏组合是多少？
6. 收益上界：scan 段占向量核时间比例 × 关键路径缩减比（O(M)→O(log M)），是否超过噪声底？
7. 高精度 dtype 若保留最强屏障，屏障计数下降（逐行→逐波）本身是否仍有收益（本例 fp32 是）？

## 验收标准（编译 / 精度 / 性能判据，含噪声底口径与回退阈值）

- **构建**：编译通过；UB 预算含 ping/pong 第二缓冲后在上限内（含与其它策略叠加的最坏组合）。
- **精度**：全量用例 PASS（本例两阶段均 23/23）；阶段一低精度 dtype 与基线逐位一致；阶段二高精度 dtype bad_ratio 不劣于基线（本例 fp32 7 case bad_ratio=0）；种子/进位边界 case（首/尾 tile、跨 tile）专项通过。
- **性能**：3 对平衡交替配对（A 侧为冻结基线重建 .so，身份写明），geomean 加速超噪声门（本例噪声门 0.5%，阶段一 2.6686x、两阶段累计 4.9283x）；低精度 case 显著加速、高精度 case 不劣化。
- **零劣化判据**：23/23 case 同向加速无回退、逐对离散 0.09% << 0.5% 噪声门；任一 case 回退超阈值即整体回退。
- **可采集性**：profiling 包裹采集下无 aicore timeout 挂死（阶段一 attempt2 教训纳入验收）。
- **归因**：不改访存语义与输出分布（除结合顺序外），收益归因于屏障强度/计数下降与关键路径深度下降。
- **回退**：精度超标 dtype 回退原串行补偿链；采集挂死回退最强屏障形态；UB 超限回退串行链；逐行窄指令树形形态禁止保留。

## 检索卡（短卡）

动作：串行 scan 链两阶段改造：链内屏障按输出 dtype 降级（低精度 PIPE_V、高精度保留 PIPE_ALL）；串行链改对数树扫描，每波单屏障、ping/pong 双缓冲。
适用：逐行串行依赖、读写集全在 UB 的 V→V 向量 scan/递推链；tile 行数多（链长）收益最大。
限制：弱屏障充分性须实证、跨流水保留 PIPE_ALL；树扫描改变结合顺序须精度兜底；种子/进位三处不可丢；禁止逐行窄指令树形。
范围：向量核 scan 段行间前缀依赖链（区别于块间归约树形合并）。
检索词：PIPE_V、PIPE_ALL、Hillis-Steele、树扫描、屏障降级、ping/pong、carry、aiv_vec。
机会：aiv_vec 为 top1 流水，scan 指令/屏障数锁死在 O(行数)；无依赖段合并饱和后 scan 仍是时长主体。
代价：UB 预算增 ping/pong 第二缓冲须重算。
