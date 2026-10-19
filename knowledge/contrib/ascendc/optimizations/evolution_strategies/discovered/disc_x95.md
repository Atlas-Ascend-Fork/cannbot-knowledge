---
type: Optimization
title: "X95: 每输出/每输出元素的 DMA 描述符数（block count）结构 KPI —— 搬运块数最小化优先于字节最小化（elementwise 广播型 + conv/im2col+GEMM 链 + 逐 token 串行 scan/SSM 三族已复现）"
description: "型（pairwise / outer-product / 广播成 [N,M]）的无归约 elementwise，基线的典型形态是"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.compute.neighborhood.convolution
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-10-13T00:00:00Z"
platforms:
  - a2
---

# Strategy X95: 广播型/笛卡尔积 elementwise 的「每输出元素 DMA 描述符数」结构 KPI

> 进化发现元数据（迁移自 cannbot-skills `references/discovered/` 原始 frontmatter）：
>
> ```yaml
> schema_version: okf.v1
> kind: discovered_strategy
> id: X95
> title: "X95: 每输出/每输出元素的 DMA 描述符数（block count）结构 KPI —— 搬运块数最小化优先于字节最小化（elementwise 广播型 + conv/im2col+GEMM 链 + 逐 token 串行 scan/SSM 三族已复现）"
> origin: discovered
> discovered_round: 1
> discovered_from: "16_iou_v2 evolution round_1/parallel_0 (node w1, workflow_guided) + 8_ConvStandard3d evolution round_1/parallel_2 (node x0, open_exploration)"
> base_speedup: "【16_iou_v2】0.2931x -> 9.5026x vs PyTorch（asc geomean 2579.08 -> 84.86us）【8_ConvStandard3d】0.5461x -> 0.6496x（asc geomean 909.47 -> 751.18us，-17.41%，n=50/50）；另有同轮的**负对照**：块数上升的方向净损失 +2.17%"
> confidence: cross_op_verified
> status: active
> op_families: [elementwise, broadcast, cv_fusion, conv, im2col, matmul, ssm, chunk-scan, recurrent, scan]
> bottlenecks: [undersize_transfer, mte3_stall, no_overlap, mte2_stall, partial_overlap, near_optimal]
> tags: [per-token-scan-family-added-2026-09-24, block-count-kpi, ~70-cycle-per-block, payload-independent-descriptor-cost, multi-block-contiguous-merge, whole-plane-single-transfer, dense-flat-strided-read-densify, a-operand-l1-residency, col-panel-width-vs-block-count, negative-control-toY-repack, row-batched-dense-store, lane-realization, deinterleave, counter-mode, flat-ub-arena, row-wise-multicore-split, outer-product, pairwise, iou, 910b2c, dav-2201, not-mix-with-x93-criterion]
> strategy_ids: [X95, X93, X94, P7, P10, P66, P84, P85, P97, P101, P105, P112, X24, X92, X97]
> reuse_stats:
>   ops: [16_iou_v2, 8_ConvStandard3d, 33_Mamba2Fwd]
>   families: [elementwise/broadcast, conv/im2col+GEMM, ssm/recurrent(per-token-scan)]
>   passed: 3
> ```

## 判定信号 / 结构 KPI

**KPI = 每输出元素的 DMA 描述符数**（不是带宽利用率、也不是 MFU）。对 `out[i][j] = f(a[i], b[j])`
型（pairwise / outer-product / 广播成 [N,M]）的无归约 elementwise，基线的典型形态是
**每列每行一条 4B store**（`out[i][j]` 各写一次）：

- 旧版（16_iou_v2 基线）：store 描述符数 = `N*M` 个 ⇒ **1.0 条/输出元素**；
- 新版（w1）：写回改成「每行 `cols` 个连续 float 一条 `DataCopyPad`（多 burst：`RBLK` 行、
  `lenBurst=cols*4B`、`dstStride=(M-cols)*4B`）」⇒ 描述符数 ≈ `N*M/cols`。
  `cols` 上限 `GEN_CT=2048`（fp32 Counter 模式一次覆盖）⇒ **最好的情形约 1 条/2048 元素**。
  > 口径说明（**保守取法**）：本卡按「每行一条描述符」计。若按"一条 `DataCopyPad` 含 `RBLK` 个
  > burst"计还可再除以 `RBLK`；原始 implementation_note 的写法是「新版 = `N*M/cols/…` 量级下降」，
  > 那个「`/…`」没有给全 ⇒ 本卡只取可确证的 `cols` 因子，不把 `/RBLK` 算进结论。

量化这个 KPI 的两条**独立**证据（同一算子）：

1. **写回侧（w1 的直接收益）**：`0.2931x → 9.5026x`（vs PyTorch，全 50 例），
   asc geomean `2579.08us → 84.86us`。同轮 `sv2` 节点把 KPI 写成设计验收值：
   「每输出元素描述符数 ≤0.125（colsTile=8）/ ≤0.031（colsTile=32）；每输出字节 ≥4B（消 8x 扇区放大）」。
2. **装载侧（sv1 的同型归因）**：纯同步消融变体实测 case3 的管道占比
   `aiv_mte2_ratio=0.709` / `aiv_vec_ratio=0.087` / `aiv_mte3_ratio=0.138` / `aiv_scalar_ratio=0.141`，
   `aiv_time≈39.7us ≈ Task Duration 43.7us` ⇒ **核一直在跑、只有 MTE2（输入装载）忙、向量单元空转 91%**。
   输入端当时的形态是「bbox/gt 各 4 次 4B/行的 strided DataCopyPad」（每行 4×rows 条描述符）——
   与写回侧同一种病。

**定序判据**：sv1 的归因消融（**只**改同步/流水结构：删列尾 2 条 `PIPE_ALL` 换
`V_MTE3`/`MTE3_V` 事件 + inter 写回双缓冲）只值 **1.16x**（同口径 asc-vs-asc `2579.08 → 2217.03us`）/
**1.30x**（5 例 per-case 探针）⇒ **主杠杆是描述符吞吐/写回访问行为，不是同步延迟暴露**。

> ⚠️ **勿与 X93 的判据混用**：X93 用「asc 吞吐跨 shape 高度一致」当描述符 bound 的指纹；
> 本算子实测每输出元素成本跨 case 变约 15 倍（0.255→3.96ns/元素），该指纹**不成立**
> （见 disc_X93 的「判据边界」节）。本卡的 KPI 是**静态计数**（数每行 DMA 条数 × burst 宽度），
> 不依赖吞吐恒定性。

## 四步做法

1. **车道真实化**（前提：先让 W 通道装满真值，再谈宽写回）。基线用 `[rows, W=8]` 且 7/8 是填充零。
   两条已验证路径：
   - w1：host 侧 `gtboxes.t().contiguous()` 一次成型**分平面 `[4, M]`** 视图，device 侧每个 gt 坐标
     一个**稠密平面**一个 dense burst —— 100% 有效通道；bbox 侧不做 `[1,CT]→[R,CT]` 广播填充，
     改用**标量-向量 op**（`Mins/Maxs` 带标量操作数），每行读一次标量覆盖整个 `cnt` 宽。
   - n1：`deinterleave4()`（一次大块读 + 4 次 `GatherMask(reduceMode=true, src1Pattern=3/4/5/6)`）
     解出 4 条连续坐标向量 + `spread8()`（Brcb）把每个坐标值展开到自己的 32B 块。
   - **为什么必须一起做**：vector 的块步长粒度是 32B，表达不了 4B 子块偏移 ⇒ 只在末列加宽 store
     而不做车道真实化不可行。
2. **写回行批 dense**：每行 `cols` 个连续 float 一条 `DataCopyPad`（多 burst，`blockCount=RBLK`），
   **UB 侧 dense、gap 只在 GM 侧**（OKF f29 硬规则；`copy_rows_out`：UB 侧 gap 0、GM 侧 `(M-cols)*4B`）。
3. **向量链一次性覆盖（Counter 模式）**：`SetMaskCount()` + `SetVectorMask<T, MaskMode::COUNTER>(cnt)`，
   12 条向量 op 全部 `repeatTimes=1` + `MASK_PLACEHOLDER` + 稠密 repeatParams（unary `{1,1,8,8}`、
   binary `{1,1,1,8,8,8}`），循环尾 `ResetMask()` + `SetMaskNorm()`。消灭每列手算 mask/repeat 与逐列控制开销。
4. **多核按输出行均分**（不是按列切条带）：`stripes = min(N, 48)`。基线按 M 列切 ⇒ case49（M=64）
   只拉起 8/48 核（实测 0.028x，全 50 例最差）；由于 `out[i][j]` 只依赖 bbox i 与 gtbox j、跨块无归约，
   **行划分是精确切分，无精度风险面**。
5. **UB 单块 flat arena + 手工 offset 分区**（P85）：arena = `GEN_PLANES*GEN_CT + GEN_RBLK*GEN_CT + GEN_RBLK*4 + 16`
   = 24608 float ≈ **98432 B（96KB / 192KB）**，**与输入 shape 无关**（旧版按 shape 静态分区 139296B）。

## 实测（16_iou_v2，Ascend910B2C / DAV_2201，AIV 路径）

| 指标 | 基线（生成核） | X95 变体（w1，交付件） |
|---|---|---|
| geomean speedup vs PyTorch（`--quick --quick-batch`，50/50） | 0.2931 | **9.5026** |
| geomean_asc_us | 2579.08 | **84.86** |
| geomean_ref_us（同口径窗口内参） | 756.00 | 806.37 |
| mean / median speedup | — | 10.27 / 9.53 |
| 逐例 min / max speedup | 0.03（case49） | **1.61 / 20.48**（全 50 例 >1x） |
| 交付口径（per-case，vs 归档标杆 **e2e**） | 0.2590 | **8.6920**（逐例 min 1.0269 / max 30.2830；n=50/50） |
| 精度 | 50/50 bit-exact vs `model.py` | **50/50 PASS**（md5 `0a5f29bdbdcb0b95b4f45c29738df00b`） |
| case 集 | — | md5 `08ef56ac340d4f599addfbd0e7a4ddd4`（50 例） |

同轮兄弟（同一 case 集、同一口径）：
- `parallel_1`（n1）**7.0594**：`[R_TILE=64, C_MAX=64]` 列块 tile + 每 tile 一条宽 2D `DataCopyPad`
  （写回描述符从 `N*M` 降到 `N*M/cols`，cols=64 时 64 倍）⇒ DMA 侧被压下后**瓶颈转到逐 tile 标量 setup**
  （单代表例 case5 采样 `aiv_scalar_ratio 0.361 ≈ aiv_vec_ratio 0.386`，`mte2 0.078 / mte3 0.100`）。
- `parallel_2`（sv1）**0.3627**（= `artifacts/lineage.jsonl` 的 `0.3626921…` 取 4 位小数；该变体自己的
  `implementation_note.txt` 与 attempt-ledger 记作 `0.36` / `0.363`，三者同源）：纯同步消融（见上）。

## 实现约束 / 踩坑（每条都是踩过的）

1. **Counter 模式必须用 `isSetMask=false` 的算子重载**（`Mins<T,false>/Maxs<T,false>/Sub<T,false>/...`）——
   模板默认 `isSetMask=true` 会用 `MASK_PLACEHOLDER`(=0) 覆盖掉 counter，元素数变 0 ⇒ **全部算空**。
2. **`cols`/`C_MAX` ≤ 64（fp32 mask 位图只有 64 位）**：n1 的列块再宽就要拆成每行多次 repeat，
   失去「一次算完一行」的简洁性。
3. **行批预读/RBLK 放大要 A/B**：w1 的 Local Refinement R1（每批 4 行的 16 个 `GetValue` 提到批首 +
   行批 4→8）在窄列 case 上改善（46 +9%、49 +7%、47 +5%），但中/大 shape 普遍退化 5~10%
   （`sc[32]` 局部数组 + 8 行全展开的寄存器/栈压力）⇒ 整轮 geomean **6.4935**（对照 9.2183/9.5026）**否决回退**。
4. **尾部 chunk 的 padding 通道会算但不写回**（只按 `cols*4B` 落盘）——元素级 op 不跨通道污染，
   由 50/50 精度验证兜住。
5. **本卡不解决 `no_overlap`**：w1 的残余瓶颈是单缓冲输出 tile 让 V 与 MTE3 串行
   （case45：`aiv_vec_fp32_ratio=0.39`、静态 V 占用 36%、268MB 输出按 1.2TB/s ≈223us 占 405us 窗口的 55%，
   有效写带宽只到 ~560–720 GB/s 约峰值一半）。双缓冲方向见 OKF f39（手写事件 ping-pong 死锁）。

## 适用场景

- **命中**：`out[i][j] = f(a[i], b[j])` 型无归约 elementwise / outer-product / 笛卡尔积广播
  （pairwise IoU/IoF、距离矩阵、相似度矩阵、attention 前的 score 外积、任何 [N,1]×[1,M] 广播），
  且输出侧是「每列每行一条小 DMA」或每行有效通道远小于向量宽度（`W` 里大部分是填充）。
- **不命中**：有归约/跨元素依赖的算子（分块不再精确）；纯复制型搬移（→ disc_X93，其修法更直接）；
  已证真带宽 bound 的算子。
- **与既有卡关系**：X93（复制型上采样：整带单条 dense DMA + 工作项上移）与 X94（可分离重采样：Gather 提升 +
  消列块循环 + 输入读一次）是同族先例，三卡的**修法**可互通，但 **X93 的判据不适用于本卡**（见上文 ⚠️）。
  向量链形态取自 X33/P84（Counter 模式一次性覆盖）、UB 分区取自 P85、切片取自 P97/P101。

## 第二来源：8_ConvStandard3d（conv / im2col+GEMM 链，四段 device kernel）

`prepare(AIV) → im2col(AIV) → gemm(MIX, 手工 fp32 Mmad) → epilogue(AIV)`，全 fp32，50 例。
本族的「描述符/块数」是**另一个量纲的同一 KPI**：这里不是一个 kernel 内的每输出元素块数，
而是**每个 core 每段 kernel 发出的 `DataCopyPad` block 总数**。

**定量法则（本卡新增的核心常数）**：把 per-core 的 block 数 × 成本去拟合各 kernel 的实测时长，
在 prepare / im2col / epilogue / gemm 四段上一致得到 **≈70 cycle / block，且与 payload 近乎无关**
——epilogue 的 130 个 512 B block 与 prepare 的 4 个 65504 B block **单块记账相同**。
⇒ 对这类「多段流水 + 每次调用固定开销」的算子，**优化目标是块数（描述符吞吐），不是字节数**。

**为什么字节账会误导（本轮实测反证）**：设备**不是** DRAM 饥饿 —— case32 合计 4266 MB / 4378 us
= 975 GB/s，对实测 1.4 TB/s 峰值只有 70%；case49 是 721 GB/s（52%）。逐 kernel 的引擎预算才是限制项：
gemm 的 AIC MTE2 = 1694 MB / 1446 us = 48.8 GB/s/core（约为本件 per-core MTE2 上限 32 B/cycle 的 85%），
epilogue = 6.9 GB/s/core（引擎在等自己的指令流），im2col = 33 GB/s/core（58%）。

**已复现的四条块数削减手法（每条的收益均已 A/B）**：

| # | 段 | 手法 | 块数变化 | 实测 |
|---|---|---|---|---|
| T1 | epilogue | 每个 (n,co,do) 任务改成**整平面一次**读/写（原来切 4 个 chunk） | 8 → 2 描述符/任务 | 并入 v1 |
| T2 | prepare | 零填充平面两侧都连续 ⇒ 塌缩成**一条多块** `DataCopyPad`（blockCount=planeP/ELEM_CAP，blockLen=65504 B，src/dst stride 0） + 一条余数 | 6 → 2（case49: 34 → 2） | 并入 v1 |
| T3 | im2col | fused-plane band 读同样合并（band 在 xp 与 UB 两侧都连续） | 2 → 1（case32）；66 → 2（case49） | 并入 v1 |
| T4 | gemm | A 操作数（wp）**整 K 常驻 L1**：`nTiles==1` 时 A 对所有 task 逐位相同，一次 `Nd2Nz` 加载（原来每 m-tile 每 K panel 重读） | 11 → 6 描述符/任务；A 的 MTE2 流**整条消失**（case32 339 MB、case37 677 MB = 整个 B 流的 50%） | 并入 v1；同一手法被同轮兄弟 n1 独立实现，单独值 -15.30% |
| T5 | epilogue | acc 读从「每 (do,ho) 一行、行内跳过 slack 的 strided gather」改成**dense flat run**（平面在 GM 里本就连续，slack 只是流的一部分） | — | `aiv_mte2_ratio` 0.987 → **0.222** |
| T6 | im2col | `COL_PANEL` 256 → **512**（配合 TM/TN/TK 128/256/64 → 64/512/32）：一条 im2col 写块 = 一个 k 行的 panel slice，块数 = `Kflat·rowRun/COL_PANEL` ⇒ panel 翻倍即块数减半 | 减半 | v3 |

**实测（8_ConvStandard3d，Ascend910B2C，全 50 例，`--quick --quick-batch --warm-up=1`，device 4）**

| 版本 | md5 | geomean_asc (us) | geomean_ref (us) | speedup | asc-vs-asc vs 父 |
|---|---|---|---|---|---|
| 父（m2） | 9aac5e16… | 909.47 | 496.65 | 0.5461 | — |
| v1 | 1059ee43… | 797.16 | 492.55 | 0.6179 | −12.35% |
| v2 | dcfaef7c… | 789.86 | 503.46 | 0.6374 | −13.15% |
| **v3（交付）** | **bd7c6ec9…** | **751.18** | **487.98** | **0.6496** | **−17.41%**（48/50 例变快） |

精度 50/50 PASS（tol 1e-3，maxdiff 0 ~ 5.722e-06）。

**负对照（本卡最强的机制证据，务必读）**：同轮 `parallel_0`（node w0）走**相反方向**——把 im2col/GEMM 的
m 轴按真实输出宽 `Wo` 重排（`colPanel = lcm(256, Wo)`）以换取 cube Fixpipe 直写 `y`，**toY 命中 4/50 → 27/50**
（acc 张量与 epilogue kernel 在这 27 例上真的消失，精度 50/50 PASS），**但端到端净损失 +2.17%**。
原因正是本 KPI：m pitch 不再是 8 的倍数后，平台的 32 B 取整 UB pitch 规则迫使 im2col 的写退化成
**每行一个 block**（blockLen = `Wo*4` = 520 B/264 B，对比基线的 1024 B mid），**块数约翻倍，吃掉的比省下的多**。
⇒ 「省字节（去 acc 往返 + 去一个 kernel）」被「块数上升」反超 —— **块数优先于字节**在这里被反方向证实。

**遗留缺陷（已定位、未修）**：v3 让 case37 单独 +7.9% —— `TN=512` 迫使 `TM=64`，`coPad=128` 于是被切成两个
co tile，B 流（col）被读两遍（+960 us）。修法：给 `coPad > TM` 的例加第二 geometry（tiling key 分发）或把 `TN` 运行期化。
另有两道结构性墙：epilogue 的「每输出行一 block」写（要 `Wpitch == Wo` 才能整平面单块，而该方向已被上面的负对照否决）、
im2col 的「每 (k,panel) 一 block」写（提高 COL_PANEL 可继续压，但会与 CASE 的 colPanel 显存/寻址耦合）。

**与前一段（elementwise）的关系**：同一 KPI 的两种尺度 —— elementwise 是「每输出元素的块数」，
本族是「每 core 每 kernel 的块数」。两者的修法都以**合并搬运 / 加大 blockLen / 提高描述符承载量**为核心，
共享 `UB 侧 dense、gap 只在 GM 侧`（f29）这条硬规则。

## 来源

- 主来源：`output/16_iou_v2_evo/round_1/parallel_0`（node `w1`，workflow_guided，sig=`[P84, P85, X25]`）；
  证据：`implementation_note.txt`（阶段 0-3 逐条 + Local Refinement 两轮否决记录）、`performance.json`、
  `evaluation_results.json`、`artifacts/lineage.jsonl`、`world_model_final.json`。
- 归因/同型证据：`output/16_iou_v2_evo/round_1/parallel_2`（sv1，装载侧管道占比）、
  `output/16_iou_v2_evo/.wm_before_r1_refine.json`（Supervisor 的 KPI 与 sv2 验收值）。
- 交付判据：`output/16_iou_v2_evo/VERDICT_16_iou_v2.md`（8.6920 / n=50 / md5 两枚）。
- **第二来源**：`output/8_ConvStandard3d_evo/8_ConvStandard3d_evo_20260923_102840/round_1/parallel_2`
  （node `x0`，open_exploration，md5 `bd7c6ec9f7105823a84703c1a2edbd54`）；证据：`implementation_note.txt`、
  `performance.json`、`precision_per_case.txt`、`evaluation_results.json`、`profiling/case{32,40}/…/op_summary_*.csv`。
- **负对照来源**：同 EVO_DIR 的 `round_1/parallel_0`（node `w0`，workflow_guided，md5 `26a150ad18ec282618bbd825c72753e1`）、
  以及同轮独立实现同一 A-常驻手法的 `round_1/parallel_1`（node `n1`，-15.30%，md5 `e4f6a67130ad02ee8500bdbac519b723`）。
- **状态说明（已升级）**：`confidence: cross_op_verified` / `status: active` —— 已在**两个不同算子族**
  （elementwise/broadcast 与 conv/im2col+GEMM）独立复现「块数/描述符数下降 ⇒ 提速」，且在本族拿到
  **反方向**的负对照（块数上升 ⇒ 净损失），机制方向性被双向证实。

## ⚠️ 判据边界：描述符数 KPI 是**诊断量**，不是普遍绑定轴（2026-09-23，8_ConvStandard3d round_3/parallel_0 补记）

同族的一次**反例式补充**（必须与本卡的 KPI 一起读）：

- round_3/parallel_0（node n8，X92 三方合并，geomean_asc 681.2658us / 0.727801x）按本卡的 KPI 做静态计数，
  **预测 im2col 的描述符数从 10,155,510 降到 2,601,750（3.90x）**，但实测 im2col **时长基本不动**
  （case32 −0.02% / case49 +2.43%）。
- 它的**真实收益来源是 L2 命中率**：GEMM 变快的同时 `aic_mte2_ratio` 反而**上升**（case32 0.520→0.657、
  case49 0.638→0.755）——faster while busier，即 B 流（col）的 L2 命中率提高，而不是描述符变少。
  同轮 chunk on/off 同窗 A/B：ON 681.2658 vs OFF 712.9848us（**−4.66%**，这一值远大于 n5 自查的 −1.00%）。

⇒ **正确的读法**：本卡的 KPI 是「先算块数账」的**筛选/诊断工具**，它能判定「搬运结构是否有浪费」，
但**不能推出「块数降了时间就会降」**。当同一段同时受 L2 命中率（或 DRAM 带宽）约束时，块数削减可能
完全不兑现为时长。落地前必须按「块数账 → 同窗 A/B 实测」两步走，禁止只用静态计数结论替代 A/B。
（16_iou_v2 的 `定序判据` 一节当时已用同步消融给出过同向证据；本补记把它从"该算子特例"升级为"普遍边界"。）

## 第三来源：33_Mamba2Fwd（逐 token 串行 scan / SSM，2026-09-24 补记）

**形态**：每核一个 (b,h) 任务、核内 `for t` 逐 token 串行递推（Mamba-2 SSD：`S_t = a_t·S_{t-1} + dt'_t·(x_t⊗B_t)`，
`y_t = S_t·C_t`）。基线每个 token 发 **5 条行 DMA**（x/B/C/z 入 + out 出，每条约 128~512B）并配 **9 对
`Set/WaitFlag`**（`MTE2_V` / `V_MTE2` / `MTE3_V` / `S_V` …）——描述符数与握手数都随 T 线性增长。

**做法**（与本卡第 2 步同型，落点从「每行一条」升到「每 token-block 一条」）：
5 条 per-token 行 DMA 合并为**块级多行 2D 突发**（`blockCount=nrows`，行距用字节 gap 表达；
`TB = min(16, T)`），全部 flag 由 per-token 上提为 **4 对/块**。

**量化（同窗同协议 A/B，非跨窗绝对数）**：

| 指标 | 基线 | 合并后 |
|---|---|---|
| 每 token DMA 指令数 | 5 | **0.31** |
| 每 token 握手对数 | 9 | **1.25** |
| 同窗 A/B | — | **1.076x**（TB=16 26.685us vs TB=0 28.700us，同一 `.so`、同一窗口、min-of-2） |

逐 case 方向一致：`c6`（fp16，`N%16!=0` 回退路径被消除）单点收益最大（43.9~44.7us → 38.6us），
`c2/c10/c11` 同向。**注意本卡 KPI 的读法**（见上一节边界）：本算子里块数削减**确实兑现**成时长，但
同算子另一变体把同一手法套到 x/z 张量的三次尝试全部在 **VEC UB 越界**处失败（40 核全崩，
UB 预算脚本核过无重叠，预算内未定位）⇒ 突发化必须先把 UB 预算与槽基址对齐算清（见下）。

**第三条边界（UB 侧语义，与 GM 侧不同）**：UB 侧 2D `DataCopyPad` 的块步进是
**`align32(blockLen) + dstStride*32`**，不是 `blockLen + dstStride*32`。这条由"43/50 例在
`xpitch > Ps` 下通过"反推得到——写 UB 多行突发时若按 GM 侧直觉算步进，会静默错列。

**来源**：33_Mamba2Fwd evolution（进化基线内核模式，3 轮×3 并行）round_2/parallel_1（node n3_s1）
与 round_2/parallel_0、round_3/parallel_0；官方 50/50 判据全过（主 agent 逐变体独立复跑）。
