---
type: Optimization
title: "已验证方案：二维 strided DMA + AR 行归约替换逐通道/逐行标量壳"
description: "把逐通道/逐行标量壳（小 DataCopyPad + ReduceSum + GetValue/SetValue）改成二维 strided DMA + AR 行归约，可一次性消除事务粒度与同步开销。"
tags:
  - task.optimization
  - topic.attention
  - topic.programming_model.execution_unit.cube
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.memory
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopyPad_GMToUB.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceSum_interface/ReduceSum.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/ppsa_2d_strided_dma_ar_row_reduce.json
    role: evidence
created_at: "2026-10-26T00:00:00Z"
updated_at: "2026-10-26T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 ppsa-2d-strided-dma-ar-row-reduce）。
>
> 原始元数据：
>
> ```yaml
> id: ppsa-2d-strided-dma-ar-row-reduce
> op_families: [reduction, elementwise, attention]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/ppsa_2d_strided_dma_ar_row_reduce.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/ppsa_2d_strided_dma_ar_row_reduce.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# 已验证方案：二维 strided DMA + AR 行归约替换逐通道/逐行标量壳

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 问题现象
5 段纯 AIV 流水（praw 通道加权归约 → softmax → 空间加权 + 行和 → LayerNorm → 门控逐元素）中，
K1/K3/K5 与 K2/K4 都写成「每个通道（或权重行）一次 `DataCopyPad(len)` + `Mul` + `ReduceSum` +
`SyncVtoS` + `GetValue` + `SetValue`」。
- 小 HW（HW<4096 → nblk=1）时 grid = B（1~8 核），每核串行 C=160~2048 次该链路；
- 特征：mte2/scalar 利用率不低但 kernel 时间极长，属「小块搬运 + 每元素一次全屏障」的标量壳。

1. **二维 strided DMA**：把逐通道拷贝换成一次
 `DataCopyPad(dst, src[c0*HW + h0], {blockCount=cb, blockLen=len*sizeof(T), srcStride=(HW-len)*sizeof(T), dstStride=0})`，
 `cb = CB_TILE = 8`（每次搬 8 行），`len = Min(TILE_R, HW-h0)`（**元素数**）。
 - **源地址必须带空间 tile 偏移 `h0`**（`src` 为未偏移的 GM tensor 时）；若 `src` 在调用前已偏移 `h0`，则不能重复加。
 例：`HW=1349, TILE_R=1024, h0=1024` 时只搬每行列 1024–1348（`len=325`），`srcStride=(1349-325)*sizeof(T)`。
 - `cb=8` 只决定一次搬多少行，**不**保证 GM 行首 32B 对齐：GM 行起点是 `c0*HW + h0 + row*HW`，
 32B 对齐取决于 `HW`/`h0`；**32B 对齐约束在 UB 侧**（`dstStride=0` 时行距 `AlignUp(blockLen,32)`）。
 GM 行首非 32B 对齐时由 `DataCopyPad` 处理，需在设备上验证。
 - `DataCopyExtParams` 在 GM→UB 方向：`blockLen` 与 `srcStride` 以**字节**计，`dstStride` 以 **32B DataBlock** 计；
 `blockLen` 必须是 `sizeof(T)` 的整数倍。
2. **AR 行归约**：`ReduceSum<float, Pattern::Reduce::AR>(dst, tile, work, {rows, cols}, true)`
 一次产出 rows 个连续行和，写回 GM 时不再逐元素 `SetValue`。
3. **Axpy 通道累加**：通道加权由逐通道 `Muls+Add` 改为 `Axpy(acc, xf[cc*ps], w[c0+cc], len)` 全行累加。
4. **权重/偏置**按 (RW_TILE × W_CW_MAX) 二维块搬入（K2/K4），行归约一次算 8 个点积。
5. host 侧 `GetReduceSumMaxMinTmpSize({rows, cols}, DP_FLOAT, AR, true, false)` 重算 reduce 临时区。

## UB 预算（实例）
CB_TILE(8) × TILE_R(1024) × 4B = 32KB 工作区 + 双缓冲输入 ≤16KB + 权重 tile 2×(8×1024×4B)=64KB
+ scan/red/work ≈ 远小于 192KB。TILE_R 从 4096 降到 1024 是为了给二维瓦片与双缓冲留空间。

## 有效范围与代价
- 适用于：沿通道/行维做大量独立小归约（GEMV、通道注意力、door 加权、per-channel 归一化）的纯 AIV 算子；
- 判据：kernel 内出现 `for c/j: DataCopyPad(小) → ReduceSum → GetValue → SetValue` 的串行链；
- 代价：UB 侧行距按 `AlignUp(blockLen,32)` 对齐；GM 行起点是否 32B 对齐取决于 `HW`/`h0`，由 DataCopyPad 处理并需设备验证；尾块 `len = Min(TILE_R, HW-h0)`；
- **非整 32B 行长验证**：建议在 fp32 `len=325`（`blockLen=1300B` → UB 行按 1312B/328 floats 对齐）与
 fp16/bf16 小奇数列上各跑一次，确认 `dstStride=0` 的 UB 行距与后续 `ReduceSum` 的 `padLast` 一致；
 若先把 fp16 数据 Cast 成 fp32 再归约，必须显式按 `AlignUp(len,8)` 个 fp32 重排行距，不能沿用源 dtype 的行距。
- **尾块偏移验证**：在 `HW=1349, TILE_R=1024, h0=1024`（`len=325`）上，用至少 2 行、各行各列填不同值的数据，
 比对 `DataCopyPad` 搬入内容与逐行 `ReduceSum` 结果都对应列 1024–1348，覆盖 `h0>0`。
- 非目标：真正的带宽饱和场景（本方案不减少总搬运量，只消除事务粒度与标量壳）。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/ppsa_2d_strided_dma_ar_row_reduce.json`；引用时请结合上文适用条件与失效边界判断适用范围。

## 后续（ 续跑）：本方案是「消标量壳」的终点，不是性能终点

K2/K4 仍是 `grid=B`（B=1~8）、K1/K3/K5 仍是 `grid=B*nblk`（1~16），

接续方案见 [`ppsa_5stage_parallel_collapse_fix.md`](ppsa_5stage_parallel_collapse_fix.md)：通道轴切片 + 消费者折叠部分和、
即：**消壳（本卡）与打满并行度（新卡）是两个正交阶段，收益近似乘性**。