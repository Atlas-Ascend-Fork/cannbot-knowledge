---
type: Guide
title: 单次矩阵乘局部输出
description: 开启Partial Output后Iterate不进行K轴累加，仅输出单次基本块计算结果，由用户自行累加。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/single_matmul_local_output.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 单次矩阵乘局部输出

## 功能介绍
单次矩阵乘局部输出，又称Partial Output。如基础知识中所述，一次Iterate计算过程中，会按K方向进行一次或多次基本块计算，其中的一次基本块计算为baseM*baseK和baseK*baseN大小的输入数据进行计算得到baseM*baseN大小的结果；每次基本块计算的结果进行累加后，便得到baseM*singleCoreK和singleCoreK*baseN大小的输入数据计算得到的结果baseM*baseN，并将其作为一次Iterate的最终结果输出。
开启Partial Output功能后，调用Iterate接口不会进行K轴累加，只进行单次基本块计算。用户可以通过GetTensorC接口获取对应的单片数据，最后自行进行K轴上的累加。
## 使用场景
矩阵乘计算结果不需要累加，只需要输出baseM*baseK和baseK*baseN的计算结果baseM*baseN。例如需要先获取单次基本块计算的数据进行反量化，再累加得到最终结果。
## 约束说明
-   该功能仅支持MDL模板。
-   获取矩阵乘计算结果时，仅支持调用Iterate和GetTensorC接口的连续写模式，不支持非连续写模式以及IterateAll接口获取计算结果，连续写模式的介绍请参考GetTensorC。
-   该功能不支持带有Bias矩阵的Matmul计算，即不支持输入Bias矩阵。

<!-- cannbot:related:start -->
## 相关

- [GetTensorC](../../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/get_tensor_c.md)（`explains`）：用户可以通过GetTensorC接口获取对应的单片数据；Iterate后，获取一块或者两块C矩阵片。场景卡要求 Partial Output 后从 GetTensorC 取得单片并自行累加 K 轴，接口卡给出 INNER/OUTER_PRODUCT 返回一片或两片的合同；联合可写出正确取片与累加循环。
<!-- cannbot:related:end -->
