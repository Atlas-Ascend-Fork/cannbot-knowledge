---
type: Guide
title: 连续计算API
description: 连续计算API，支持Tensor前n个数据计算。针对源操作数的连续n个数据进行计算并连续写入目的操作数，解决一维tensor的连续计算问题。
tags: [task.lookup, topic.implementation.api_layer]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/library_api/basic_api/interface_classification/continuous_compute_api.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 连续计算API

连续计算API，支持Tensor前n个数据计算。针对源操作数的连续n个数据进行计算并连续写入目的操作数，解决一维tensor的连续计算问题。
下图以矢量加法为例，展示了连续计算API的特点。

<!-- cannbot:related:start -->
## 相关

- [Copy](../../../../../apis/simd_api/basic_api/memory_vector_compute/data_move/copy_ub_to_ub_continuous.md)（`explains`）：Copy 与《连续计算API》的实质衔接是：该 Copy 是 32B 对齐的 UB 连续搬运；DataCopy 对应入口、UB-UB 搬运指南、AscCopy 与非 VL 掩码故障共同说明通路、对齐和尾块边界。
- [连续计算（SIMD计算）](../../../../../apis/simd_api/basic_api/memory_vector_compute/simd_compute/continuous_compute.md)（`explains`）：连续计算API 与《连续计算（SIMD计算）》的实质衔接是：连续计算 API 与高维切分的选择取决于布局连续性，非对齐优化给出连续但未对齐时的可执行分支。
- [连续非对齐场景优化](../../../../operator_practice/simd_operator_optimization/vector_compute/vf_optimization/continuous_unaligned_optimization.md)（`related`）：连续计算API 与《连续非对齐场景优化》的实质衔接是：连续计算 API 与高维切分的选择取决于布局连续性，非对齐优化给出连续但未对齐时的可执行分支。
- [高维切分API](high_dim_split_api.md)（`same_topic`）：连续计算API 与《高维切分API》的实质衔接是：连续计算 API 与高维切分的选择取决于布局连续性，非对齐优化给出连续但未对齐时的可执行分支。
<!-- cannbot:related:end -->
