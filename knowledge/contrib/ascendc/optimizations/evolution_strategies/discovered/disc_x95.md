---
type: Optimization
title: "X95: 每输出/每输出元素的 DMA 描述符数（block count）结构 KPI —— 搬运块数最小化优先于字节最小化（elementwise 广播型 + conv/im2col+GEMM 链 + 逐 token 串行 scan/SSM 三族已复现）"
description: "广播型/笛卡尔积 elementwise 及多段搬运链的优化应优先最小化每输出/每核的 DMA 描述符数，而非字节数。把逐行小 burst 合并为行块 dense 写回、车道真实化、整平面单条多块搬运可显著降低描述符数；该 KPI 是诊断量，需同窗 A/B 验证，块数下降不必然兑现为时长。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.compute.neighborhood.convolution
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X95: 广播型/笛卡尔积 elementwise 的「每输出元素 DMA 描述符数」结构 KPI

## 判定信号 / 结构 KPI

**KPI = 每输出元素的 DMA 描述符数**（不是带宽利用率）。对 `out[i][j] = f(a[i], b[j])`
型（pairwise / outer-product / 广播成 [N,M]）的无归约 elementwise，基线的典型形态是
**每列每行一条 4B store**（`out[i][j]` 各写一次）：

- 旧版：store 描述符数 = `N*M` 个 ⇒ **1.0 条/输出元素**；
- 新版：写回改成「每行 `cols` 个连续 float 一条 `DataCopyPad`（多 burst：`RBLK` 行、
  `lenBurst=cols*4B`、`dstStride=(M-cols)*4B`）」⇒ 描述符数 ≈ `N*M/cols`。
  `cols` 上限 `GEN_CT=2048`（fp32 Counter 模式一次覆盖）⇒ **最好的情形约 1 条/2048 元素**。
  > 口径说明（**保守取法**）：本卡按「每行一条描述符」计。若按「一条 `DataCopyPad` 含 `RBLK` 个
  > burst」计还可再除以 `RBLK`；本卡只取可确证的 `cols` 因子，不把 `/RBLK` 算进结论。

量化这个 KPI 的两条**独立**证据：

1. **写回侧**：描述符合并带来数量级收益；而纯同步/流水消融（只改同步结构、不改访问行为）
   只值较小的固定比例 ⇒ **主杠杆是描述符吞吐/写回访问行为，不是同步延迟暴露**。
2. **装载侧**：纯同步消融变体显示 `aiv_mte2_ratio` 高、`aiv_vec_ratio` 低，核一直在等输入装载、
   向量单元空转；输入端的形态是「每个输入行多次 4B/行的 strided DataCopyPad」
   —— 与写回侧同一种病。

**定序判据**：同步消融只解释小部分收益，而描述符合并解释主要收益 ⇒ 先做描述符/访问行为，
再考虑同步与流水。

> ⚠️ **勿与 X93 的判据混用**：X93 用「asc 吞吐跨 shape 高度一致」当描述符 bound 的指纹；
> 对每输出元素成本跨形状变化大的算子该指纹**不成立**（见 X93 的「判据边界」节）。
> 本卡的 KPI 是**静态计数**（数每行 DMA 条数 × burst 宽度），不依赖吞吐恒定性。

## 四步做法

1. **车道真实化**（前提：先让 W 通道装满真值，再谈宽写回）。基线常用窄通道且大部分是填充零。
   两条已验证路径：
   - host 侧 `gtboxes.t().contiguous()` 一次成型**分平面 `[4, M]`** 视图，device 侧每个坐标
     一个**稠密平面**一个 dense burst —— 全部有效通道；bbox 侧不做 `[1,CT]→[R,CT]` 广播填充，
     改用**标量-向量 op**（`Mins/Maxs` 带标量操作数），每行读一次标量覆盖整个 `cnt` 宽。
   - `deinterleave4()`（一次大块读 + 4 次 `GatherMask(reduceMode=true, src1Pattern=3/4/5/6)`）
     解出 4 条连续坐标向量 + `spread8()`（Brcb）把每个坐标值展开到自己的 32B 块。
   - **为什么必须一起做**：vector 的块步长粒度是 32B，表达不了 4B 子块偏移 ⇒ 只在末列加宽 store
     而不做车道真实化不可行。
2. **写回行批 dense**：每行 `cols` 个连续 float 一条 `DataCopyPad`（多 burst，`blockCount=RBLK`），
   **UB 侧 dense、gap 只在 GM 侧**（`copy_rows_out`：UB 侧 gap 0、GM 侧 `(M-cols)*4B`）。
3. **向量链一次性覆盖（Counter 模式）**：`SetMaskCount()` + `SetVectorMask<T, MaskMode::COUNTER>(cnt)`，
   12 条向量 op 全部 `repeatTimes=1` + `MASK_PLACEHOLDER` + 稠密 repeatParams（unary `{1,1,8,8}`、
   binary `{1,1,1,8,8,8}`），循环尾 `ResetMask()` + `SetMaskNorm()`。消灭每列手算 mask/repeat 与逐列控制开销。
4. **多核按输出行均分**（不是按列切条带）：`stripes = min(N, 48)`。按列切在 M 小时只拉起少量核；
   由于 `out[i][j]` 只依赖 bbox i 与 gtbox j、跨块无归约，**行划分是精确切分，无精度风险面**。
5. **UB 单块 flat arena + 手工 offset 分区**（P85）：arena = `GEN_PLANES*GEN_CT + GEN_RBLK*GEN_CT + GEN_RBLK*4 + 16`，
   **与输入 shape 无关**（按 shape 静态分区会随 shape 增长而膨胀）。

## 实现约束 / 踩坑（每条都是踩过的）

1. **Counter 模式必须用 `isSetMask=false` 的算子重载**（`Mins<T,false>/Maxs<T,false>/Sub<T,false>/...`）——
   模板默认 `isSetMask=true` 会用 `MASK_PLACEHOLDER`(=0) 覆盖掉 counter，元素数变 0 ⇒ **全部算空**。
2. **`cols`/`C_MAX` ≤ 64（fp32 mask 位图只有 64 位）**：列块再宽就要拆成每行多次 repeat，
   失去「一次算完一行」的简洁性。
3. **行批预读/RBLK 放大要 A/B**：把每批多行的 `GetValue` 提到批首、行批加深，在窄列形状上可能改善，
   但中/大 shape 可能因局部数组与全展开的寄存器/栈压力而退化 ⇒ 必须全量 A/B，不能只看窄列收益。
4. **尾部 chunk 的 padding 通道会算但不写回**（只按 `cols*4B` 落盘）——元素级 op 不跨通道污染，
   由全量精度验证兜住。
5. **本卡不解决 `no_overlap`**：残余瓶颈是单缓冲输出 tile 让 V 与 MTE3 串行。
   双缓冲方向需注意手写事件 ping-pong 死锁。

## 适用场景

- **命中**：`out[i][j] = f(a[i], b[j])` 型无归约 elementwise / outer-product / 笛卡尔积广播
  （pairwise IoU/IoF、距离矩阵、相似度矩阵、attention 前的 score 外积、任何 [N,1]×[1,M] 广播），
  且输出侧是「每列每行一条小 DMA」或每行有效通道远小于向量宽度（`W` 里大部分是填充）。
- **不命中**：有归约/跨元素依赖的算子（分块不再精确）；纯复制型搬移（→ X93，其修法更直接）；
  已证真带宽 bound 的算子。
- **与既有卡关系**：X93（复制型上采样：整带单条 dense DMA + 工作项上移）与 X94（可分离重采样：Gather 提升 +
  消列块循环 + 输入读一次）是同族先例，三卡的**修法**可互通，但 **X93 的判据不适用于本卡**（见上文 ⚠️）。
  向量链形态取自 X33/P84（Counter 模式一次性覆盖）、UB 分区取自 P85、切片取自 P97/P101。

## 同一 KPI 的第二种尺度：conv / im2col+GEMM 链（四段 device kernel）

`prepare(AIV) → im2col(AIV) → gemm(MIX, 手工 fp32 Mmad) → epilogue(AIV)`，全 fp32。
本族的「描述符/块数」是**另一个量纲的同一 KPI**：这里不是一个 kernel 内的每输出元素块数，
而是**每个 core 每段 kernel 发出的 `DataCopyPad` block 总数**。

**定量法则**：把 per-core 的 block 数 × 成本去拟合各 kernel 的时长，在 prepare / im2col / epilogue / gemm
四段上一致得到 **每 block 成本近乎固定、且与 payload 近乎无关** —— 大 block 与极小 block 的单块记账相同。
⇒ 对这类「多段流水 + 每次调用固定开销」的算子，**优化目标是块数（描述符吞吐），不是字节数**。

**为什么字节账会误导**：设备**不是** DRAM 饥饿 —— 合计流量往往明显低于峰值带宽。
逐 kernel 的引擎预算才是限制项：gemm 的 AIC MTE2 接近 per-core 上限，epilogue 的引擎在等自己的指令流，
im2col 介于两者之间。

**已复现的块数削减手法**：

- **epilogue**：每个 (n,co,do) 任务改成**整平面一次**读/写（原来切多个 chunk）。
- **prepare**：零填充平面两侧都连续 ⇒ 塌缩成**一条多块** `DataCopyPad`
  （`blockCount=planeP/ELEM_CAP`，`src/dst stride 0`）+ 一条余数。
- **im2col**：fused-plane band 读同样合并（band 在 xp 与 UB 两侧都连续）。
- **gemm**：A 操作数（wp）**整 K 常驻 L1**：`nTiles==1` 时 A 对所有 task 逐位相同，
  一次 `Nd2Nz` 加载（原来每 m-tile 每 K panel 重读）；A 的 MTE2 流整条消失。
- **epilogue**：acc 读从「每 (do,ho) 一行、行内跳过 slack 的 strided gather」改成**dense flat run**
  （平面在 GM 里本就连续，slack 只是流的一部分）。
- **im2col**：`COL_PANEL` 翻倍（配合 TM/TN/TK 调整）：一条 im2col 写块 = 一个 k 行的 panel slice，
  块数 = `Kflat·rowRun/COL_PANEL` ⇒ panel 翻倍即块数减半。

**负对照（本卡最强的机制证据，务必读）**：同族反向方向——把 im2col/GEMM 的
m 轴按真实输出宽 `Wo` 重排（`colPanel = lcm(256, Wo)`）以换取 cube Fixpipe 直写 `y`，
toY 命中率大幅提高（acc 张量与 epilogue kernel 在多数例上消失，且不引入精度失败），**但端到端净损失**。
原因正是本 KPI：m pitch 不再是 8 的倍数后，平台的 32 B 取整 UB pitch 规则迫使 im2col 的写退化成
**每行一个 block**（`blockLen = Wo*4`，远小于基线的大 block），**块数约翻倍，吃掉的比省下的多**。
⇒ 「省字节（去 acc 往返 + 去一个 kernel）」被「块数上升」反超 —— **块数优先于字节**在这里被反方向证实。

**遗留缺陷**：当 `TN` 增大迫使 `TM` 减小时，`coPad` 可能被切成两个 co tile，B 流（col）被读两遍。
修法：给 `coPad > TM` 的例加第二 geometry（tiling key 分发）或把 `TN` 运行期化。
另有两道结构性墙：epilogue 的「每输出行一 block」写（要 `Wpitch == Wo` 才能整平面单块，而该方向已被上面的负对照否决）、
im2col 的「每 (k,panel) 一 block」写（提高 COL_PANEL 可继续压，但会与该段的 colPanel 显存/寻址耦合）。

**与前一段（elementwise）的关系**：同一 KPI 的两种尺度 —— elementwise 是「每输出元素的块数」，
本族是「每 core 每 kernel 的块数」。两者的修法都以**合并搬运 / 加大 blockLen / 提高描述符承载量**为核心，
共享 `UB 侧 dense、gap 只在 GM 侧` 这条硬规则。

## 判据边界：描述符数 KPI 是**诊断量**，不是普遍绑定轴

同族的一次反例式补充（必须与本卡的 KPI 一起读）：

- 静态计数可能预测 im2col 的描述符数大幅下降（例如数倍），但运行时长基本不动。
- 真实收益来源可能是 **L2 命中率**：GEMM 变快的同时 `aic_mte2_ratio` 反而**上升**
  （faster while busier）——B 流（col）的 L2 命中率提高，而不是描述符变少。

⇒ **正确的读法**：本卡的 KPI 是「先算块数账」的**筛选/诊断工具**，它能判定「搬运结构是否有浪费」，
但**不能推出「块数降了时间就会降」**。当同一段同时受 L2 命中率（或 DRAM 带宽）约束时，块数削减可能
完全不兑现为时长。落地前必须按「块数账 → 同窗 A/B」两步走，禁止只用静态计数结论替代 A/B。

## 同一 KPI 的第三种尺度：逐 token 串行 scan / SSM

**形态**：每核一个 (b,h) 任务、核内 `for t` 逐 token 串行递推（Mamba-2 SSD：`S_t = a_t·S_{t-1} + dt'_t·(x_t⊗B_t)`，
`y_t = S_t·C_t`）。基线每个 token 发 **5 条行 DMA**（x/B/C/z 入 + out 出，每条较小）并配 **9 对
`Set/WaitFlag`**（`MTE2_V` / `V_MTE2` / `MTE3_V` / `S_V` …）——描述符数与握手数都随 T 线性增长。

**做法**（与本卡第 2 步同型，落点从「每行一条」升到「每 token-block 一条」）：
5 条 per-token 行 DMA 合并为**块级多行 2D 突发**（`blockCount=nrows`，行距用字节 gap 表达；
`TB = min(16, T)`），全部 flag 由 per-token 上提为 **4 对/块**。

**读法**：该形态下块数削减**确实兑现**成时长；但同算子另一变体把同一手法套到 x/z 张量的尝试
全部在 **VEC UB 越界**处失败（即使静态 UB 预算无重叠，也可能在预算内失败）⇒ 突发化必须先把 UB 预算与
槽基址对齐算清。

**第三条边界（UB 侧语义，与 GM 侧不同）**：UB 侧 2D `DataCopyPad` 的块步进是
**`align32(blockLen) + dstStride*32`**，不是 `blockLen + dstStride*32`。写 UB 多行突发时若按 GM 侧直觉
算步进，会静默错列。

## 验证方法

- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
- 描述符类改动额外做静态块数账（每行/每核 DMA 条数 × burst 宽度），并用 pipe 占比与同窗 A/B 交叉验证块数下降是否兑现为时长。

## 补充判据（跨算子复核）

- **panel 预取 P=4 的收益来自“对齐 + 合并发射”，不是单纯加深**：一次 GM→L1 装 4 个连续 K-tile 的 A/B panel，A 行段按 1024B 对齐；K=7168 时 GM→L1 发射数从 56 降到 14。
- **容量口径**：A1/B1 在 L1（512KB），不是 UB（192KB）；P=4 时 A1=128KB + B1=256KB = 384KB < 512KB。此前“192KB 互斥”是误判。P=3 基本持平，P=4 才 +5.0%。
