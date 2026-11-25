---
type: Optimization
title: "X112: shift/gather-sum 的行块广播 MAC（消除逐行标量壳与窄段 DMA）"
description: "把「分支权重 × 位移张量求和」类内核从逐行小 DMA + 窄 repeat 乘加，改写为行块工作单元 + 一条 level-0 广播 MAC；判断依据是指令形状与同步次数受限，而不是 DMA 总量或 burst 大小。"
tags:
  - task.optimization
  - topic.attention
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.memory
  - topic.compute.reduction
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopyPad_GMToUB.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/basic_api/aux_data_structures/BinaryRepeatParams.md
    role: constraint
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x112.json
    role: evidence
created_at: "2026-10-26T00:00:00Z"
updated_at: "2026-10-26T00:00:00Z"
platforms:
  - a2
---
> 证据：基线/变体与逐 case 数据见 [证据包 cases/disc_x112.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x112.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# Strategy X112: shift/gather-sum 的行块广播 MAC（消除逐行标量壳与窄段 DMA）

## 核心思路

「把分支权重 × 位移张量求和」这类算子（滑窗位移加权、门控加权聚合、gather-sum）常被写成
**逐行标量驱动**：每行一次小 DMA + 一次窄 lane 向量乘加 + 一次全流水同步。
这类内核可能是 **inner-loop-shape-bound**（指令形状受限），而不是 DMA 总量或 burst 大小受限：

- 事务粒度：按 quarter 段搬，小通道数时每段只有很少元素，DMA 事务极短；
- 指令形状：逐行 `Mul`+`Add`，每次 repeat 只覆盖少数有效 lane，任务内大量全流水排空。

改写为 **行块（row-block）工作单元 + 广播 MAC**：

1. 一次二维 `DataCopyPad`（`blockCount=nr`、`blockLen=lc*sizeof(T)`、`srcStride` 为字节）
   把 `nr` 行 × `lc` 通道搬进 UB（GM 侧按字节步长，UB 侧按 32B 对齐紧密排布）；
2. 用 **一条** level-0 `Mul`/`MulAddDst`，`repeatTimes=nr`、`src1RepStride=0`，并传**显式位图 mask**
   与 `BinaryRepeatParams(1,1,1,repS,repS,0)`，让硬件把「每通道权重向量」广播到 `nr` 行；
   **注意**：level-2 `Mul` 的 `repeat + src1RepStride=0` 组合在另一场景中出现数值错误（见 F29），
   成功条件必须写成「level-0 + 位图 mask + 完整 repeat 参数」；
3. 多个分支在**同一块 fp32 tile** 内累加，最后统一 cast + 落盘；边界列改成 strided 多行组，
   不要让单核串行扫整列；
4. 一个行块只留 4 个 barrier（搬入 / V / 搬出 / 下一块预取）。

**总流量不变**，收益全部来自事务粒度、指令数与同步次数。

## 问题现象

逐行标量驱动的典型形态：`for row: DataCopyPad(小) → 向量乘加 → 全流水同步`。
特征是 mte2/scalar 利用率不低，但 kernel 时间极长、等效带宽远低于 HBM 峰值——
成本不在字节数，而在**事务数量 × 每次同步/发射的固定开销**。边界列若按单核串行扫整列，
小 W 的 case 会被大量单行处理拖死。

## ⚠️ load-bearing 坑：level-0 向量 API 的 `mask` 是元素个数而非 lane 位图

`SetMask(int32_t len)` 语义是「本次 repeat 处理多少个元素」。若按直觉传位图，会打开整个 repeat
窗口，导致相邻 repeat 的 `dstRepStride` 块互相覆盖——症状是**多数 case 偶然通过、少数失败**，
且错误通道恰好切在段边界上。正确做法是传 `uint64_t mask[2]` 数组形式（MASK_BIT_MODE），
使每个 repeat 只写目标块。Cos/Sin 等末尾调用过 `SetMaskNorm()` 的场景同样要显式改回位图数组。

## 适用场景

- 滑窗位移/门控加权求和、gather-sum、per-channel 权重乘加、通道注意力加权聚合；
- 症状判据：kernel 里出现逐行小 `DataCopyPad` + 窄 repeat 乘加 + 频繁全流水同步，
  且等效带宽远低于 HBM 峰值；
- 跨算子复用：**行内等距栅格的 2D DMA + 广播 MAC**（把「每 head 一次小 DMA + 一次小 Mul」
  改成整行一条 2D `DataCopyPad` + level-0 广播，把 cos/sin 模式广播到全部 head）；
  以及**行块化归约**（ReduceSum 走 `repeatTimes=rows` 批量、每行结果独占 32B slice）；
- 非目标：已经用多行 2D DMA + 双缓冲做过一遍、只剩事务粒度问题的内核（收益递减）。

## 实现要点

- `nr`（行块大小）按 UB 预算算：`nr = (UB_budget - acc - row) / (2 * lc * sizeof(T))`（双缓冲）；
- `lc` 取整段（一个 quarter 一次搬），host 侧把 `lc` 上取整到满足 512B 传输的长度；
- 权重常驻 UB，按 chunk 更新；普通 `TBuf` 权重缓冲需显式 `HardEvent::V_MTE2` 再发下一 chunk 的 DMA
  （`TQue` 不代管裸 TBuf 的跨 pipe 依赖，漏了表现为**随机**精度错）。

## 边界与反例

- 若内核已经消除逐行小 DMA、只剩段宽/事务粒度问题，本策略收益有限；
- 广播 MAC 必须用 level-0 + 位图 mask；level-2 `Mul` 的 `repeat + src1RepStride=0` 组合不可直接套用（F29）；
- 与 X116 的分工：X112 负责「把逐行指令形状变成行块/广播形状」，X116 负责「把逐次 DMA 往返变成
  批处理 + 一次等待」；两者叠加时才拿到完整收益。

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/disc_x112.json`；引用时请结合上文适用条件与失效边界判断适用范围。

