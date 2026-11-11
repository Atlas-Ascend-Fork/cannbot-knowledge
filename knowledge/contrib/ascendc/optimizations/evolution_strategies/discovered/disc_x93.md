---
type: Optimization
title: "X93: 复制型上采样的『UB 布局重排 + 整带单条 dense DMA』——把 H 轴复制烘焙进 Gather 偏移表、工作项上移到输入平面"
description: "纯复制型重采样（nearest / repeat / kron 型）的输出是输入沿空间轴的整数倍复制，基线常退化为每输出行/每元素一条小 DMA。把 H 轴复制烘焙进 Gather 偏移表、工作项上移到输入平面，并用整带单条 dense DMA 写回，可把描述符开销转为带宽。"
tags:
  - task.optimization
  - topic.data_movement.layout_transform
  - topic.data_movement
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X93: 复制型上采样的「UB 布局重排 + 整带单条 dense DMA」

## 判定信号

算子是**纯复制型重采样**——输出对输入是各空间轴的**整数倍复制**（nearest / repeat / kron 型，
输出元素集合 = 输入元素集合的倍数拷贝，零算术强度）。fingerprint：`msprof` 的 `task_time` 显示 asc 吞吐
**跨 shape 高度一致**且远低于可达峰值带宽。这种「跨 shape 恒定」就是**每输出行/每元素一条 DMA
描述符开销 bound** 的指纹（带宽 bound 会随 shape 浮动，描述符 bound 不会）。

对照：参考核若在同一批形状上接近峰值带宽，即参考核吃的是带宽，基线吃的是指令/描述符。
**判定该不该用本卡只需这一个对比**。

## 判据边界

- 「跨 shape 恒定」是本卡**自身形态**（纯复制型搬移、零算术强度、输出/输入体积比恒定）上的指纹，
  **不是描述符粒度受限的必要条件**；**不得反向使用** —— 观测到吞吐随 shape 浮动，不足以排除
  「每输出元素一条 DMA 描述符」的机制。
- 当吞吐恒定性不成立时，改做**每输出元素 DMA 描述符数 / 每 burst 覆盖字节数**的静态计数
  （数 kernel 里每行的 DMA 条数与 burst 宽度），或用管道占比（`aiv_mte2_ratio` / `aiv_mte3_ratio`）定序，
  不要用吞吐恒定性一票否决。
- **本卡的修法不受此边界影响**：UB 密排 staging、整带单条 dense DMA、工作项上移到输入平面这三步
  仍可整套借用。

## 三步做法

设复制轴为 D/H/W，各自倍率 `d_rep/h_rep/w_rep`（本卡不要求三轴相等，只要求**整数倍**）。

### 1. 工作项上移到「共享只读张量」的维度（= D 轴复用）
基线的工作单元是**输出**平面（`n_tasks = N*C*D_out`），于是同一个输入平面被（对 D 轴倍率个输出平面）
各加载 + 各展开一遍。改为 job = **一个输入平面** `(n, c, m)`：它喂养的输出平面恰是**连续区间**
`od ∈ [ceil(m*d_out/d_in), ceil((m+1)*d_out/d_in))`，D 轴复制退化为纯 MTE3 扇出 ——
**MTE2 与 Vector 的有效工作量直接除以 d_rep**。这是 X66「工作项上移到共享张量维度」在
复制型算子上的特化形态（X66 针对 map/索引表，本卡针对被复制的数据张量本身）。

### 2. 把 H 轴复制「烘焙」进 Gather 的偏移表
不要「同一展开行发 h_rep 次写回」（那是 h_rep 条 DMA）。把 staging 的列偏移表长度取 `h_rep * W_out`，
**尾部重复头部**（表按 `(w_in, w_out, h_rep, elem_bytes)` 在 host 侧缓存）：一条输入行走一次 Gather，
直接产出 **h_rep 份首尾相接的 W 展开行**。于是 H 轴复制的成本从 `h_rep` 条 MTE3 变成 0 条（并进 Gather 的
读偏移），而 Gather 的读量不变（`h_rep*W_out` 是必然的展开输出量）。

### 3. 整带一条连续 DMA（双侧 dense）
因为 H 复制已烘焙进 staging，一个行 band `[q0, q0+nb)` 的 staging **逐元素等于**该输出平面的输出行
`[q0*h_rep, (q0+nb)*h_rep)` 首尾相接 —— 所以每个输出平面每 band 只需**一条** `blockCount=1`、**零 stride**
的 `DataCopyPad`（UB dense → GM dense，「UB 侧必须 dense」由构造满足）。输入侧同理：输入行在 GM 连续，
且 `w_in*sizeof(T)` 是 32B 整数倍时行在 UB 里也天然对齐，整带一条 DMA 载入。

## 实现约束（每条都是踩过的）

1. **`DataCopyExtParams` 的 stride 是「相邻块之间的 gap」，不是块的绝对偏移** —— `srcStride=0` 会让源**前进**
   而不是重复读同一行。想写「同一行重复 N 次」必须先在 UB 内把行复制成 N 份密排槽位，再发
   `blockCount=N / srcStride=0 / dstStride=0`。直接从单行 UB 源发 `blockCount=N` 会越过行槽读到相邻数据，
   症状是 **maxdiff 为输出量级的常量**（不是舍入）。本卡的「整带 blockCount=1 纯 dense」形态
   从构造上绕开了这个陷阱 —— 这也是它比「多块 DataCopyPad」更稳的原因。
2. **Gather 的 count 上限**：`AscendC::Gather` 的 count 形态内部按 repeat 走，单次 count ≤1024 元素
   （count>1024 会静默重复 offset 索引）。`h_rep*W_out > 1024` 时按 1024 切块，块边界保持 32B 倍数。
3. **offset 表的 `srcBaseAddr` 是相对 src LocalTensor 基址的字节偏移**
   （`offsetAddr = (uint64_t)srcLocal + srcBaseAddr`），行选择交给 `srcBaseAddr`、列选择交给偏移表，
   这样同一张表可被所有行复用。
4. **`PipeBarrier<PIPE_ALL>` 不能整段删净**：去掉 k 迭代边界的 `PIPE_ALL` 后，
   单次执行逐位正确、连续发射也可能正确，**但 kernel 退出时 MTE3 仍有在飞 DMA**，随后任何
   `torch.npu.empty_cache()` 会**永久挂死**。这是事后任何单次精度/性能测试都看不见的缺陷；
   判据是「连跑 + empty_cache」而不是单跑。要么补回边界 barrier，要么把在飞 DMA 显式等到退役。
5. **AIV_ONLY 发射未落地（X75 的边界）**：`KERNEL_TYPE_AIV_ONLY` + 手工双缓冲 ping-pong 在
   **已带手工事件编排**的 kernel 上不自动成立，可能出现设备侧空转挂死 —— 需独立同窗口 A/B，不可照搬。
   本卡回退到基线已验证的 `MIX_AIC_1_2` + event id 立即配对模式。代价是 V 与 MTE3 目前串行
   （store 占总流量大头），**后续最值得补的一步**是输出双缓冲。
6. **前提与回退**：快速路径要求 `h_out % h_in == 0`（H 复制可整带写）且 `w_in*sizeof(T) % 32 == 0`
   （行在 UB 内天然对齐）。不满足时**自动回退逐行路径**（逐行载入 + 单行 W 展开 + 逐输出行写回），
   保证通用 shape 正确性。

## 适用场景

- **命中**：任何「输出 = 输入沿 ≥1 个轴的整数倍复制」的纯搬移算子 —— nearest 上采样（1D/2D/3D）、
  `repeat_interleave`、`kron` 型构造、pixel_shuffle/unshuffle 的复制侧、以及「广播到更大 shape 的常量展开」。
- **不命中**：非整数倍（需真正插值，含算术）、数据相关采样（remap/warp/grid_sample，见 X66/X70）、
  输出元素集合 = 输入元素集合的纯地址重排（transpose/permute → conversion 族）。
- **与本卡冲突**：若算子已被证明是**真带宽 bound**（跨 shape 吞吐随 shape 浮动且接近峰值），本卡收益趋零 ——
  先做判定信号里的「跨 shape 恒定 vs 浮动」对比再动手。

## 验证方法

- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
- 复制型搬移额外做「连续发射 + empty_cache」压力测试，确认 kernel 退出时无在飞 DMA；并覆盖整数倍与非整数倍回退路径。
