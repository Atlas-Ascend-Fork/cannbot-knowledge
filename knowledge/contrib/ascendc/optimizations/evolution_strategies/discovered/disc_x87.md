---
type: Optimization
title: "Grouped 量化 matmul 的 ND-int32 路由 + 行块批处理 epilogue（GroupedMatmulSwigluQuantV2）"
description: "分组 int8 matmul + fp32 域 SwiGLU + per-token requant 的 CV 融合算子，两级结构性改造叠加：(1) 把 Cube 输出 C 由 NZ 路由为 ND int32（NZ 碎片重组与逐行 64B strided DataCopyPad 整体删除，epilogue 直读连续行）；(2) epilogue 从「逐 token 行」改为「RB 行成块」——一次 2D DataCopyPad（blockCount=RB, blockLen=No*4, srcStride=(N-No)*4, dstStride=0）取连续 RB 行，Cast/scale/Silu/Mul/Abs/Div/clamp/存各只跑一次 over RB*No lanes，每行指令数 ~18 → ~(2*RB+25)/RB。全 50 例 geomean 0.0233x → 0.7924x（geomean 报出；同窗口 A/B 相对上一轮最优 0.57x → 0.78x = 1.37x），50/50 精度通过。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.compute.quantization
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-10-13T00:00:00Z"
platforms:
  - a2
---

# Strategy X87: Grouped 量化 matmul 的 ND-int32 路由 + 行块批处理 epilogue

> 进化发现元数据（迁移自 cannbot-skills `references/discovered/` 原始 frontmatter）：
>
> ```yaml
> schema_version: okf.v1
> kind: discovered_strategy
> id: X87
> origin: discovered
> title: Grouped 量化 matmul 的 ND-int32 路由 + 行块批处理 epilogue（GroupedMatmulSwigluQuantV2）
> description: 分组 int8 matmul + fp32 域 SwiGLU + per-token requant 的 CV 融合算子，两级结构性改造叠加：(1) 把 Cube 输出 C 由 NZ 路由为 ND int32（NZ 碎片重组与逐行 64B strided DataCopyPad 整体删除，epilogue 直读连续行）；(2) epilogue 从「逐 token 行」改为「RB 行成块」——一次 2D DataCopyPad（blockCount=RB, blockLen=No*4, srcStride=(N-No)*4, dstStride=0）取连续 RB 行，Cast/scale/Silu/Mul/Abs/Div/clamp/存各只跑一次 over RB*No lanes，每行指令数 ~18 → ~(2*RB+25)/RB。全 50 例 geomean 0.0233x → 0.7924x（geomean 报出；同窗口 A/B 相对上一轮最优 0.57x → 0.78x = 1.37x），50/50 精度通过。
> confidence: two_independent
> status: active
> op_families: ['matmul', 'moe', 'quantization', 'cv_fusion']
> bottlenecks: ['undersize_transfer', 'scalar_loading', 'no_overlap', 'mte2_stall', 'compute_bound']
> tags: ['grouped-matmul', 'moe', 'quantization', 'swiglu', 'nd-route', 'nz-drain-defect', 'row-block-batching', 'vector-instruction-amortization', 'epilogue-fusion', 'device-side-schedule']
> strategy_ids: [X10, X11, X23, X26]
> discovered_round: 1
> discovered_from: round_1/parallel_0 (n1) + round_2/parallel_2 (x0_x1) + round_3/parallel_0 (n1_s2)
> base_speedup: 0.0233x → 0.8060x/0.8164x vs PyTorch（50 例全量，geomean；两次独立测量，已达 0.8x 目标）
> ```

## 核心思路
GroupedMatmulSwigluQuant（V2 融合：grouped int8 matmul → fp32 dequant → SwiGLU → per-token int8 requant）这类
「Cube 主干 + 重向量 epilogue」的算子上，加速来自**两级结构改造**，而不是调 tiling 常数：

1. **C 输出路由 ND int32（承接 X11/canonical D3）**：把 `MatmulType<GM, CubeFormat::NZ, int32_t>` 改为
   `CubeFormat::ND`。基线在 NZ 下要对每个 token 行发 `2*n1` 个 **64 B** 的 `DataCopyPad`
   （`blockCount=n1, blockLen=64, srcStride=(16*aM-16)*4`，stride 可达数百 KB），ND 之后同一行是连续的，
   NZ 碎片重组代码可整体删除。注意 host 的 `SetCType` 必须与 kernel 模板 C 一致（混配即 507015）。
2. **epilogue 行块批处理（本轮新手法）**：epilogue 的成本不是算力而是**向量指令条数**。
   基线每条 token 行发 ~18 条向量指令（每条后面还跟一个 `PipeBarrier<PIPE_V>`），
   在 M=196608 时每 AIV 核约 7.4 万条指令 → 指令延迟受限。
   改为 RB 行成块：一次 2D `DataCopyPad` 取连续 RB 行（两半各一次），
   其后 Cast / weight_scale / x_scale / Silu / Mul / Abs / Div / clamp / Cast / store
   **各只跑一次 over RB*No lanes**，每块指令数 ~(2*RB+25)，即 ~18/行 → ~2.7/行。
   absmax 折叠同时改成行数无关（chunk-split `Max`，`mask=64`，`repeatTimes=RB`，`repStride=No/8`，再 mask 32/16/8）。

## 适用场景
- grouped/deep-K 量化 matmul + 逐行（per-token）向量后处理（dequant / 激活 / requant）的 CV 融合算子。
- 判定前置：task_time 显示 AIV epilogue 是 AIC matmul 的数倍（本例基线 5–31×），
  且 epilogue 的瓶颈是**指令条数/行**而非算力；`No_`（每行有效列数）不太大时行块批处理的 RB 可以取大。
- 规模边界：`No_` 大（本例 N≥1536）时算子转为 **cube-bound**（case47 N=2560: 322 GFLOP int8 ≈ 1.17 ms @ ~268 TOPS），
  行块批处理收益趋零，剩余空间只在 cube 侧（baseN 512 / L1 IBShare / L2 tile sizing）。

## 实现要点
- `blockCount=RB, blockLen=No*4, srcStride=(N-No)*4, dstStride=0`：**两半分开取**是让批处理可表达的关键
  （缓冲内半行 stride 非均匀，无法一次取整行）。
- `DataCopyPad` UB→GM 的 `srcStride` 单位是 **32 B 而不是字节**。
- absmax 折叠需要 32 B 对齐偏移；把行宽 pad 到 2 的幂会浪费大量 UB（No_=1280 时浪费 60%），
  pad 到 align-64 更优（本例 RB 6→8、fold 工作量下降）。
- 取数必须用 **expert 内行偏移**（`r = i - sg[g]`），不是全局 token 行。
- VEC 前缀运算在 sub-32B 元素数上会 507015 崩溃（这也是 absmax 尾部停在 8 lane 标量读的原因）。
- host 守卫（如 `M <= aiv*1024`）常常是**某个 UB 缓冲尺寸 bug 的绕过**：本例真因是 `bYs_`（y_scale staging）固定 1024 float、
  而行循环写 `rpc = ceil(M/nb)` 个元素，M>49152 即越界。修法是分段 flush 让 UB 占用与 M 解耦，而不是维持守卫。

## 追加：Cube 侧「让框架自导 L1 计划」而不是 pin singleCoreM/N（round_3/parallel_0，+3.2%）
当 epilogue 被压到原语下限后，剩余空间在 cube 侧。**不要**沿用「GetTiling 之后手工 pin singleCoreM/singleCoreN」的写法
（那会冻结 L1 窗口）。改为在 host 侧：
`SetShape(singleM, singleN, K)` + `SetOrgShape(...)` + `SetFixSplit(baseM, baseN, baseK)` + `SetBufferSpace(512KB, 128KB)`，
让 `MatmulApiTiling` 自己推导 L1 计划，再做合法性校验（被拒则回退旧 builder）。
最优默认落在 `singleM = baseM = 128, singleN = 512` ⇒ 框架把 **A 的整条 K 轴钉在 L1**
（K=2560 时 `stepKa=20, depthA1=20` ⇒ 320KB A + 128KB B / 512KB），A 的重读次数从 `N/256` 降到 `N/512`。
kernel 侧同步把 `singleCoreN` 从编译期常量 `GMSQ_TILE_N` 改为读 `tiling->singleCoreN`（本例 4 处），
并把 expert plane 的行 pad 一起抬到 `GMSQ_MAX_TILE_M` 以免多 N-tile 时越界。
**指纹**：per-K 的 asc 增益随 K 单调上升（K=256 −1.9% → K=2560 +10.8%），这是 A 命中 L1 的特征。
**边界（均实测证伪）**：`singleM > baseM`（如 1024/512）会让 `GetTiling` 把 L1 K 窗口退回 `depthA1=2` 并串行 16 个 base tile ⇒ 0.5239x 大回退；
int32 acc 在 128KB L0C 下 `M_eff·N_eff ≤ 32768`，纯 base 形状调优上限约 5.7%；int32 下 `baseN=512` 不可行（会逼 `baseM≤64`，反而多 50% 重载）。
同窗口 A/B（device4，ref 349.48 vs 351.22us 差 0.5%）：0.8060x vs 上一轮最优 0.7808x = **+3.2%**。

## 判定纪律：先用 op_summary 的 pipe 比值定位，再决定改哪条管（round3 实证修正）
`msprof --quick --quick-batch` 的 `op_summary_*.csv` **是带 pipe 比值列的**（不要以为 quick 模式没有）：
`aic_mac_ratio / aic_mte2_ratio / aiv_vec_ratio / aiv_scalar_ratio / aiv_mte2_ratio`。
本例（GroupedMatmulSwigluQuantV2，row-block epilogue 已完成后）实测：
- `gmsq_post_kernel`(AIV)：**`aiv_scalar_ratio` 0.68–0.90**、`aiv_vec_ratio` 0.42、`aiv_mte2_ratio` 仅 0.05–0.13
  ⇒ **epilogue 是标量管受限，不是 DMA 受限**；靶点是「折叠后的向量结果 `GetValue` 出来 + 7 段标量 max 链」的 per-token absmax
  （`scalar_reduce_after_vector`），对应 P94/P95/P99/P100/X23/X26。
- `gmsq_mm_kernel`(AIC)：`aic_mte2_ratio` 0.78、`aic_mac_ratio` 0.12 ⇒ MTE2 受限（A/B 的 L1 重载）。
- epilogue 约占 wall 时间的 45%（7654.6 µs mm vs 6236.7 µs post）。
三个只动向量管/DMA 的候选（去行内 `PipeBarrier<PIPE_V>` 0.7893、requant 改倒数乘 0.7690、同 stream 分块交错 0.7378）
全部不过 +2% 条——**先读 pipe 比值再动手，可以省掉这三轮**。
另：实测双 ACL stream + event 的真并发会破坏 quick-batch 的 `stream_id → case` 归因并引发跨 case 竞态（16/50 精度失败）；
任何 overlap 方案必须是**单个 MIX kernel**。

## 来源
自动发现于 6_GroupedMatmulSwigluQuantV2 进化：round_1/parallel_0（node n1）= 0.5639x（ND 路由 + 单遍 epilogue + baseM 128 + 解除 M 守卫），
round_2/parallel_2（node x0_x1）= 0.7924x（行块批处理 epilogue）；两路独立实现同一手法家族。
round_3/parallel_0（node n1_s2）= 0.8060x/0.8164x（cube 侧让框架自导 L1 计划，singleN=512 使 A 的 K 轴常驻 L1）。
同窗口 A/B（同设备同工具的相邻窗口）：round_1 最优 0.57x → round_2 最优 0.78x（+1.37x）→ round_3 最优 0.8060x（+3.2%）；三段 ref 列互差 <0.6%。
