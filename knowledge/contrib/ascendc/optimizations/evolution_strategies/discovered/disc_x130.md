---
type: Optimization
title: "X130: 微 matmul 的「向量 API 调用数定律」与单扫点积（原 K 布局 + MulAddDst repeat 广播）"
description: "微小 shape 的（反量化）matmul 在纯 AIV 路径上主要受「向量 API 调用次数」支配；用原 K 布局 + MulAddDst repeat 广播做单扫点积，可显著减少指令条数。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.compute.reduction
  - topic.precision
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/basic_api/aux_data_structures/BinaryRepeatParams.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/vector_compute/low_latency_instruction.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x130.json
    role: evidence
created_at: "2026-11-06T00:00:00Z"
updated_at: "2026-11-06T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 X130）。
>
> 原始元数据：
>
> ```yaml
> id: X130
> origin: discovered
> confidence: single_op
> op_families: [matmul, quantization]
> bottlenecks: [compute_bound, scalar_compute, no_overlap]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/disc_x130.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x130.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# Strategy X130: 微 matmul 的「向量 API 调用数定律」与单扫点积（原 K 布局 + MulAddDst repeat 广播）

## 核心思路

小 shape 的（反量化）matmul（全部 100 case：M≤128、K≤512、N≤512、MAC≤16.8M、内核 4.9-208us）在纯 AIV 路径上
**与算力、带宽都无关，而是线性于「向量 API 调用次数」**（实测约 32-44 cycle/次固定开销）。目标函数应改成
「每核向量指令条数」。三个可叠加动作：

1. **权重保留原始 K 布局**：nibble 交织用一次 **strided `Cast`**（blockLen=16 元素、dstStride 32 元素）免费完成，
 免 low/high 两趟 pass、免 Interleave；x 整行连续搬运，点积只扫一遍 K。
2. **`MulAddDst` 的 repeat + `src0RepStride=0` 广播**：每 64 元素 chunk 由「nCnt 条 `Mul`」压成 **1 条**，
 乘积直接累加进 64-lane 累加器；`WholeReduceSum` 每行一次（原为每 chunk 一次）。
3. **输出合并为一次 2-D `DataCopy`**，替代每行一次 `V_MTE3` drain。

## 适用场景

- 量化/反量化 matmul、GEMV/GEMM 的微小 shape 段（launch-bound，最小 case 贴 ~4.9us 设备地板）
- 命中判据：`aiv_vec_ratio` 与 `aiv_scalar_ratio` 同时偏高、`aiv_mte2_ratio` 很低（本案 0.742 / 0.497 / 0.029）
- 反向判据：大 shape 计算主导且已走 `MatmulImpl`/cube 时无意义

## 实现要点

1. w 交织靠 strided `Cast`，不要为 x 做 nibble 拆分加载
2. `MulAddDst` 的 `repeat` 上限 255，K 大时分段；广播依赖 `src0RepStride=0`
3. 输出先落 32B 对齐的 accStride 行，再单次 2-D `DataCopy`
4. per-(n,blk) scale 仍需 X25/P99 向量展开（本策略只把 scale 调用数减半），二者可叠加

## 约束与坑

- **VEC 目的地址必须 32B 对齐**：per-block 部分和按 `blk*4B` 偏移累加触发 `aivec` fault（硬证实）；8-float 槽位膨胀顶爆 wBuf
- 非对齐 N（fp16/bf16 且 N%16≠0）的 `DataCopyPad` pad 溢出跨行 → 跨核 race（基线因此强制 mBlocks=1）

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/disc_x130.json`；引用时请结合上文适用条件与失效边界判断适用范围。

