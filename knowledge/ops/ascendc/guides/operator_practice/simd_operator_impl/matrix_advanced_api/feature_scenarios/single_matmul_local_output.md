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

- [GetTensorC](../../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/get_tensor_c.md)（`explains`）：《GetTensorC》说明Iterate后获取C矩阵分片，可输出到GM或UB，支持同步与异步两种模式。；《单次矩阵乘局部输出》说明开启Partial Output后Iterate不进行K轴累加，仅输出单次基本块计算结果，由用户自行累加。。二者在Iterate产出的C分片必须按同步或异步GetTensorC协议搬出，并在异步模式等待完成后才能复用资源上存在可执行的直接衔接。
- [Iterate](../../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/iterate.md)（`explains`）：单次矩阵乘局部输出 与《Iterate》的实质衔接是：Partial Output 只允许 MDL 的 Iterate+GetTensorC 连续写，跳过 K 累加且禁用 Bias/IterateAll；Matmul Kernel、异步/对齐和精度材料直接约束该链。
- [Matmul Kernel侧接口](../../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/matmul_kernel.md)（`explains`）：单次矩阵乘局部输出 与《Matmul Kernel侧接口》的实质衔接是：Partial Output 只允许 MDL 的 Iterate+GetTensorC 连续写，跳过 K 累加且禁用 Bias/IterateAll；Matmul Kernel、异步/对齐和精度材料直接约束该链。
- [Matmul特性介绍](matmul_features.md)（`same_topic`）：单次矩阵乘局部输出 与《Matmul特性介绍》的实质衔接是：Partial Output 只允许 MDL 的 Iterate+GetTensorC 连续写，跳过 K 累加且禁用 Bias/IterateAll；Matmul Kernel、异步/对齐和精度材料直接约束该链。
- [含有Matmul高阶API的算子精度问题](../../../../programming_guide/appendix/faq/matmul_advanced_api_precision.md)（`same_topic`）：单次矩阵乘局部输出 与《含有Matmul高阶API的算子精度问题》的实质衔接是：Partial Output 只允许 MDL 的 Iterate+GetTensorC 连续写，跳过 K 累加且禁用 Bias/IterateAll；Matmul Kernel、异步/对齐和精度材料直接约束该链。
- [启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖](../../../simd_operator_optimization/pipeline_scheduling/enable_iterate_avoid_sync.md)（`same_topic`）：单次矩阵乘局部输出 与《启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖》的实质衔接是：Partial Output 只允许 MDL 的 Iterate+GetTensorC 连续写，跳过 K 累加且禁用 Bias/IterateAll；Matmul Kernel、异步/对齐和精度材料直接约束该链。
- [多核对齐切分](multi_core_aligned_split.md)（`same_topic`）：多核对齐切分 与《单次矩阵乘局部输出》的实质衔接是：对齐切分按可用核数设置 SetDim/NumBlocks，并与非对齐尾块、N 对齐、Channel 拆分、多核 K 切分及临时空间计算共同决定实际 Matmul 分工。
- [异步场景处理](async_scenario.md)（`same_topic`）：单次矩阵乘局部输出 与《异步场景处理》的实质衔接是：Partial Output 只允许 MDL 的 Iterate+GetTensorC 连续写，跳过 K 累加且禁用 Bias/IterateAll；Matmul Kernel、异步/对齐和精度材料直接约束该链。
- [矩阵乘输出的N方向对齐](matmul_output_n_alignment.md)（`same_topic`）：单次矩阵乘局部输出 与《矩阵乘输出的N方向对齐》的实质衔接是：Partial Output 只允许 MDL 的 Iterate+GetTensorC 连续写，跳过 K 累加且禁用 Bias/IterateAll；Matmul Kernel、异步/对齐和精度材料直接约束该链。
<!-- cannbot:related:end -->
