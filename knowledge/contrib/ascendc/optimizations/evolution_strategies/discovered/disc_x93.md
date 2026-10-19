---
type: Optimization
title: "X93: 复制型上采样的『UB 布局重排 + 整带单条 dense DMA』——把 H 轴复制烘焙进 Gather 偏移表、工作项上移到输入平面"
description: "算子是纯复制型重采样——输出对输入是各空间轴的整数倍复制（nearest / repeat / kron 型，输出元素集合 = 输入元素集合的倍数拷贝，零算术强度）。"
tags:
  - task.optimization
  - topic.data_movement.layout_transform
  - topic.data_movement
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-10-13T00:00:00Z"
platforms:
  - a2
---

# Strategy X93: 复制型上采样的「UB 布局重排 + 整带单条 dense DMA」

> 进化发现元数据（迁移自 cannbot-skills `references/discovered/` 原始 frontmatter）：
>
> ```yaml
> schema_version: okf.v1
> kind: discovered_strategy
> id: X93
> title: "X93: 复制型上采样的『UB 布局重排 + 整带单条 dense DMA』——把 H 轴复制烘焙进 Gather 偏移表、工作项上移到输入平面"
> origin: discovered
> discovered_round: 1
> discovered_from: "15_upsample_nearest3d evolution, round_1/parallel_2 (node x0, open_exploration)"
> base_speedup: "0.4492x -> 1.2520x vs PyTorch（50/50 例，asc geomean 1275.96 -> 457.81us，-64.1%；min 0.821 / max 2.626，无例低于目标）"
> confidence: single_op
> status: active
> op_families: [gather, index_scatter, elementwise, cv_fusion]
> bottlenecks: [undersize_transfer, mte3_stall, no_overlap]
> tags: [upsample, nearest, replication, integer-scale, band-dense-dma, gather-offset-table-baked-h-rep, work-item-to-input-plane, sub-32b-descriptor-overhead, 910b2c, dav-2201, pure-data-movement, criterion-boundary, fingerprint-not-necessary, borrow-fix-not-criterion]
> strategy_ids: [X93, X66, X87, P33, P56, X26, P1]
> ```

## 判定信号

算子是**纯复制型重采样**——输出对输入是各空间轴的**整数倍复制**（nearest / repeat / kron 型，
输出元素集合 = 输入元素集合的倍数拷贝，零算术强度）。fingerprint：`msprof task_time.csv` 显示 asc 吞吐
**跨 shape 高度一致**且远低于实测峰值带宽 —— 本例 15_upsample_nearest3d 在大 case 上恒定 **~391 GB/s
（910B2C 实测峰值 1.3 TB/s 的 30%）**，跨 case 波动 <1%。这种"跨 case 恒定"就是**每输出行/每元素一条 DMA
描述符开销 bound** 的指纹（带宽 bound 会随 shape 浮动，描述符 bound 不会）。

对照：参考核（ops-cv 手写 AscendC）在同一批 case 上达 800–1175 GB/s（峰值的 62–90%），即参考核吃的是带宽，
基线吃的是指令/描述符。**判定"该不该用本卡"只需这一个对比**。

## ⚠️ 判据边界（2026-09-22 增量，来源：16_iou_v2 evolution）

> ⚠️ **矛盾标记**：`16_iou_v2`（pairwise IoU/iof 的 outer-product elementwise）实测**每输出元素成本跨 case 变约 15 倍**，
> 与上节"跨 shape 高度一致"的指纹相左。原作者（该轮 Supervisor）原话：
> 「X93 的判据要求『asc 吞吐跨 shape 高度一致』，本算子实测每元素成本跨 case 变 15 倍（0.255→3.96ns）
> ⇒ 该指纹在本算子**不成立**，X93 只能借其修法不能借其判据，不能据此断言纯描述符 bound」
> （源 `output/16_iou_v2_evo/.wm_before_r1_refine.json` 的 Supervisor 段）。

两个端点（源 `output/16_iou_v2_evo/baseline_profiling.log` 逐例 asc 耗时，除以该例输出元素数）：

| case | 输入 shape | 输出元素数 | asc us | ns/输出元素 |
|---|---|---|---|---|
| 45 | `[8192, 4]` | 8192×8192 = 67,108,864 | 17135.90 | ≈0.255 |
| 49 | `[65536, 4]` | 65536×64 = 4,194,304 | 16587.60 | ≈3.95 |

（ns/元素一列为上两列相除的**推导值**，非原始记录；15 倍 = 3.95 / 0.255。）

**本卡据此认定的边界**：
1. 上节的「跨 case 恒定」是本卡**自身形态**（纯复制型搬移、零算术强度、输出/输入体积比恒定）上的指纹，
   **不是描述符粒度受限的必要条件**；**不得反向使用** —— 观测到吞吐随 shape 浮动，不足以排除
   "每输出元素一条 DMA 描述符"的机制。
2. 该不该用本卡：当吞吐恒定性不成立时，改做**每输出元素 DMA 描述符数 / 每 burst 覆盖字节数**的静态计数
   （数 kernel 里每行的 DMA 条数与 burst 宽度），或用管道占比（`aiv_mte2_ratio` / `aiv_mte3_ratio`）定序，
   不要用吞吐恒定性一票否决。
3. **本卡的修法不受此边界影响**：UB 密排 staging、整带单条 dense DMA、工作项上移到输入平面这三步
   仍可整套借用（同族 `16_iou_v2` 正是靠"行批 dense 写回 + 车道真实化"把 store 侧描述符数从
   N×M 条降到约每行一条，见 OKF 新卡 X95）。

> 本节与上节**并存**（未覆盖原判据）：本卡在其自身形态上的实测结论仍成立，本节只收窄它的**判据适用范围**。

## 三步做法

设复制轴为 D/H/W，各自倍率 `d_rep/h_rep/w_rep`（本例三轴恒 2，但本卡不要求三轴相等，只要求**整数倍**）。

### 1. 工作项上移到「共享只读张量」的维度（= D 轴复用）
基线的工作单元是**输出**平面（`n_tasks = N*C*D_out`），于是同一个输入平面被（对 D 轴倍率个输出平面）
各加载 + 各展开一遍。改为 job = **一个输入平面** `(n, c, m)`：它喂养的输出平面恰是**连续区间**
`od ∈ [ceil(m*d_out/d_in), ceil((m+1)*d_out/d_in))`，D 轴复制退化为纯 MTE3 扇出 ——
**MTE2 与 Vector 的有效工作量直接除以 d_rep**（本例减半）。这是 OKF X66「工作项上移到共享张量维度」在
复制型算子上的特化形态（X66 针对 map/索引表，本卡针对被复制的数据张量本身）。

### 2. 把 H 轴复制「烘焙」进 Gather 的偏移表
不要"同一展开行发 h_rep 次写回"（那是 h_rep 条 DMA）。把 staging 的列偏移表长度取 `h_rep * W_out`，
**尾部重复头部**（表按 `(w_in, w_out, h_rep, elem_bytes)` 在 host 侧缓存）：一条输入行走一次 Gather，
直接产出 **h_rep 份首尾相接的 W 展开行**。于是 H 轴复制的成本从 `h_rep` 条 MTE3 变成 0 条（并进 Gather 的
读偏移），而 Gather 的读量不变（`h_rep*W_out` 是必然的展开输出量）。

### 3. 整带一条连续 DMA（双侧 dense）
因为 H 复制已烘焙进 staging，一个行 band `[q0, q0+nb)` 的 staging **逐元素等于**该输出平面的输出行
`[q0*h_rep, (q0+nb)*h_rep)` 首尾相接 —— 所以每个输出平面每 band 只需**一条** `blockCount=1`、**零 stride**
的 `DataCopyPad`（UB dense → GM dense，OKF f29「UB 侧必须 dense」由构造满足）。输入侧同理：输入行在 GM 连续，
且 `w_in*sizeof(T)` 是 32B 整数倍时行在 UB 里也天然对齐，整带一条 DMA 载入。
→ 本例大 case 每 lane 的 DMA 条数从 **~3 万条 2KB** 降到 **几百条 32~120KB**。

## 实测（15_upsample_nearest3d，Ascend910B2C / DAV_2201，AIV 路径）

| 指标 | 基线 | X93 变体 |
|---|---|---|
| geomean_speedup（vs PyTorch，全 50 例） | 0.4492 | **1.2520**（2.79x） |
| geomean_asc_us | 1275.96 | **457.81**（-64.1%） |
| geomean_ref_us（同窗口内参） | 573.19 | 573.19（逐位一致 ⇒ 窗口干净） |
| 逐例 speedup min / max | 0.320 / 0.707 | **0.821 / 2.626**（无例低于目标） |
| 精度 | — | **50/50 PASS, 50/50 BITEXACT** |

分母口径：`npu_benchmark/level3` 归档 ops-cv 手写 AscendC `UpsampleNearest3d`（50 例 geomean 567.3798us）；
本算子上 PyTorch `F.interpolate(...,'nearest')` 与它走同一个核，故 vs-PyTorch 与 vs-参考核一致。
同轮兄弟 `n7`（归族 index-scatter workflow，同族但逐行写回 + 单输入行一次 Gather）落在 **1.1317**，
差异来源正是本卡的 **第 2 步**（H 复制烘焙表）与 **第 1 步**（输入平面复用）。

## 实现约束（每条都是踩过的）

1. **`DataCopyExtParams` 的 stride 是「相邻块之间的 gap」，不是块的绝对偏移** —— `srcStride=0` 会让源**前进**
   而不是重复读同一行。想写"同一行重复 N 次"必须先在 UB 内把行复制成 N 份密排槽位，再发
   `blockCount=N / srcStride=0 / dstStride=0`。直接从单行 UB 源发 `blockCount=N` 会越过行槽读到相邻数据，
   症状是 **maxdiff 为输出量级的常量**（正是 OKF f29 形态，不是舍入）。本卡的"整带 blockCount=1 纯 dense"形态
   从构造上绕开了这个陷阱 —— 这也是它比"多块 DataCopyPad"更稳的原因。
2. **Gather 的 count 上限**：`AscendC::Gather` 的 count 形态内部按 repeat 走，单次 count ≤1024 元素
   （OKF disc_X70 记录 count>1024 会静默重复 offset 索引）。`h_rep*W_out > 1024` 时按 1024 切块，块边界保持 32B 倍数。
3. **offset 表的 `srcBaseAddr` 是相对 src LocalTensor 基址的字节偏移**（`kernel_operator_vec_gather_impl.h`：
   `offsetAddr = (uint64_t)srcLocal + srcBaseAddr`），行选择交给 `srcBaseAddr`、列选择交给偏移表，
   这样同一张表可被所有行复用（OKF P33 在 dav_c220 上的真源语义）。
4. **`PipeBarrier<PIPE_ALL>` 不能整段删净（OKF f21 的复制型特化）**：去掉 k 迭代边界的 `PIPE_ALL` 后，
   单次执行逐位正确、连续 3 次发射也正确，**但 kernel 退出时 MTE3 仍有在飞 DMA**，随后任何
   `torch.npu.empty_cache()` 会**永久挂死**（进程阻塞、AICore 0%）。这是事后任何单次精度/性能测试都看不见的缺陷；
   判据是"连跑 + empty_cache"而不是单跑。要么补回边界 barrier，要么把在飞 DMA 显式等到退役。
5. **AIV_ONLY 发射未落地（与 OKF x75 的边界）**：本例按 x75 试 `KERNEL_TYPE_AIV_ONLY`（40 lane）
   + 手工双缓冲 ping-pong 时设备侧 AICore 99% 空转挂死，回退基线已验证的 `MIX_AIC_1_2` + event id 立即配对模式。
   即 x75 的"纯向量 CANN 直编内核应声明 AIV_ONLY"在**已带手工事件编排**的 kernel 上不自动成立 ——
   需独立同窗口 A/B，不可照搬。代价是 V 与 MTE3 目前串行（store 占总流量 8/9），**后续最值得补的一步**
   （预期再 1.3~1.8x）。
6. **前提与回退**：快速路径要求 `h_out % h_in == 0`（H 复制可整带写）且 `w_in*sizeof(T) % 32 == 0`
   （行在 UB 内天然对齐）。不满足时**自动回退逐行路径**（逐行载入 + 单行 W 展开 + 逐输出行写回），
   保证通用 shape 正确性 —— 本算子 50 例全部满足，通用性靠回退分支兜住。

## 适用场景

- **命中**：任何"输出 = 输入沿 ≥1 个轴的整数倍复制"的纯搬移算子 —— nearest 上采样（1D/2D/3D）、
  `repeat_interleave`、`kron` 型构造、pixel_shuffle/unshuffle 的复制侧、以及"广播到更大 shape 的常量展开"。
- **不命中**：非整数倍（需真正插值，含算术）、数据相关采样（remap/warp/grid_sample，见 X66/X70）、
  输出元素集合 = 输入元素集合的纯地址重排（transpose/permute → conversion 族）。
- **与本卡冲突**：若算子已被证明是**真带宽 bound**（跨 case 吞吐随 shape 浮动且接近峰值），本卡收益趋零 ——
  先做判定信号里的"跨 case 恒定 vs 浮动"对比再动手。

## 来源

自动发现于 15_upsample_nearest3d evolution，round_1/parallel_2（node x0，open_exploration，未读策略库）。
同轮另一条路线 `n7`（index-scatter 归族 workflow）独立命中同族的"多块 DataCopyPad + band 化事件"形态（1.1317），
两条路线的差异点即本卡第 1、2 步。
