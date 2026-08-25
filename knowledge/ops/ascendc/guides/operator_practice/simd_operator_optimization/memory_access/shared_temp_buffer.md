---
type: Guide
title: 算子与高阶API共享临时Buffer
description: 【描述】如果算子使用的高阶API需要传入临时Buffer，如SoftMax，该临时空间会挤占算子其他计算的空间，从而导致单次计算搬运的数据量变少，搬运的次数变多。此场景可通过共享临时Buffer空间，提升单次搬运的数据量，减少搬运的次数，提升内存使用效率。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/memory_access/shared_temp_buffer.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 算子与高阶API共享临时Buffer

【优先级】高
【描述】如果算子使用的高阶API需要传入临时Buffer，如SoftMax，该临时空间会挤占算子其他计算的空间，从而导致单次计算搬运的数据量变少，搬运的次数变多。此场景可通过共享临时Buffer空间，提升单次搬运的数据量，减少搬运的次数，提升内存使用效率。
【反例】
SoftMax高阶API计算需要临时Buffer空间，算子在进行其他计算时拥有独立临时Buffer。UB空间是固定的，假设可以给SoftMax和Add能分配临时空间为64KB，SoftMax计算需要的临时Buffer空间tmpSoftmaxBuf占用32KB，则存储Add计算结果的LocalTensor tmpSumBuf最多只能分配32KB。如果src0Tensor计算的数据量是512KB，则需要搬运512 / 32 =  16次。
【正例】
SoftMax高阶API计算需要临时Buffer空间，算子在进行其他计算时可以共享此临时Buffer，按照上述假设只需要搬运512 / 64 =  8次。

<!-- cannbot:related:start -->
## 相关

- [SoftMax Tiling使用说明](../../../../apis/simd_api/adv_api/activation_functions/soft_max_interface/soft_max_tiling_usage.md)（`explains`）：指南通过 SoftMax 与 Add 共享 UB 临时空间把单次搬运容量从 32KB 提到 64KB、搬运次数从 16 次降到 8 次；SoftMax Tiling 使用说明给出先查询最小/最大临时空间、再以剩余可用空间生成 tiling 的具体接口契约。
<!-- cannbot:related:end -->
