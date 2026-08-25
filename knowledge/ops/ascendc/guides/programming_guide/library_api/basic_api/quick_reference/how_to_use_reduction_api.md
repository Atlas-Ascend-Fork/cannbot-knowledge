---
type: Guide
title: 如何使用归约计算API
description: 归约指令将数据集合简化为单一值或者更小的集合。按照归约操作的数据范围的不同，归约指令分为以下几种，可参考归约指令示意图：
tags: [task.lookup, topic.implementation.api_layer]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/library_api/basic_api/quick_reference/how_to_use_reduction_api.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 如何使用归约计算API

归约指令将数据集合简化为单一值或者更小的集合。按照归约操作的数据范围的不同，归约指令分为以下几种，可参考[归约指令示意图](#zh-cn_topic_0000002267504648_fig16735034112710)：

-   ReduceMax/ReduceMin/ReduceSum：对所有的输入数据做归约操作，得到最大值和最大值索引/最小值和最小值索引/数据总和。
-   ReduceRepeat：对每个repeat内的输入数据做归约操作，根据模板参数`ReduceType`指定求最大值/最小值/求和，得到每个repeat内的最大值和最大值索引/最小值和最小值索引/数据总和。返回索引时返回的是repeat内部索引。
-   ReduceDataBlock：对每个DataBlock内的输入数据做归约操作，根据模板参数`ReduceType`指定求最大值/最小值/求和，得到每个DataBlock内的最大值/最小值/数据总和。
-   ReducePairElem：对相邻两个（奇偶）元素进行归约操作，当前仅支持根据模板参数`ReduceType::SUM`求和，例如（a1, a2, a3, a4, a5, a6...），归约后结果为（a1+a2,  a3+a4,  a5+a6, ......）。

**图1**  归约指令示意图

针对归约指令，和其他的基础API一样也提供了**tensor高维切分计算**接口，可充分发挥硬件优势，支持开发者控制指令的**迭代执行**和操作数的**地址间隔**，功能更加灵活。但具体参数的单位和约束与基础API略有不同，下文将对这些差异点进行介绍。

-   **mask**：用于控制每次迭代内参与计算的元素，mask参数的使用方法和基础API通用的使用方法一致。
-   **repeatTime**：迭代次数，开发者通过repeatTime来配置迭代次数，从而控制指令的多次迭代执行。
    -   ReduceMax/ReduceMin/ReduceSum对于repeatTime超过255的情况，在API内部进行了处理，所以repeatTime支持更大的取值范围，保证不超过int32_t最大值的范围即可。
    -   ReduceRepeat/ReduceDataBlock/ReducePairElem和其他基础API一样，repeatTime要求不超过255。
-   **repeatStride**：表示相邻迭代间的地址步长。
    -   ReduceMax/ReduceMin/ReduceSum指令的目的操作数会归约成一个最大值/最小值/总和，所以其目的操作数不支持配置repeatStride。仅源操作数支持repeatStride，其含义、单位（datablock）和基础API通用说明一致。
    -   ReduceRepeat/ReduceDataBlock/ReducePairElem源操作数和目的操作数都支持配置repeatStride，源操作数repeatStride的含义、单位（DataBlock）和基础API通用说明一致。

<!-- cannbot:related:start -->
## 相关

- [ReduceMax接口](../../../../../apis/simd_api/adv_api/reduction_operations/reduce_max_interface/reduce_max_interface.md)（`explains`）：如何使用归约计算API说明归约指令将数据集合简化为单一值或者更小的集合。按照归约操作的数据范围的不同，归约指令分为以下几种，可参考归约指令示意图：。
- [ReduceMin](../../../../../apis/simd_api/basic_api/memory_vector_compute/reduction_compute/reduce_min.md)（`explains`）：ReduceMin 与《如何使用归约计算API》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
- [归约操作](../../../../../apis/simd_api/adv_api/reduction_operations/reduction_operations.md)（`explains`）：如何使用归约计算API 与《归约操作》的实质衔接是：该指南解释 ReduceMax/Min/Sum、Repeat、DataBlock、PairElem 的粒度以及 mask/repeat 参数；基础/Reg 总览、辅助配置和 padding/count 故障直接影响选型与结果正确性。
- [归约计算](../../../../../apis/simd_api/basic_api/memory_vector_compute/reduction_compute/reduction_compute.md)（`explains`）：如何使用归约计算API 与《归约计算》的实质衔接是：该指南解释 ReduceMax/Min/Sum、Repeat、DataBlock、PairElem 的粒度以及 mask/repeat 参数；基础/Reg 总览、辅助配置和 padding/count 故障直接影响选型与结果正确性。
- [归约计算](../../../../../apis/simd_api/basic_api/reg_vector_compute/reduction_compute/reduction_compute.md)（`explains`）：如何使用归约计算API 与《归约计算》的实质衔接是：该指南解释 ReduceMax/Min/Sum、Repeat、DataBlock、PairElem 的粒度以及 mask/repeat 参数；基础/Reg 总览、辅助配置和 padding/count 故障直接影响选型与结果正确性。
- [归约计算概述](../../../../../apis/simd_api/basic_api/memory_vector_compute/reduction_compute/introduction.md)（`explains`）：如何使用归约计算API 与《归约计算概述》的实质衔接是：该指南解释 ReduceMax/Min/Sum、Repeat、DataBlock、PairElem 的粒度以及 mask/repeat 参数；基础/Reg 总览、辅助配置和 padding/count 故障直接影响选型与结果正确性。
- [归约计算辅助配置接口](../../../../../apis/simd_api/basic_api/memory_vector_compute/reduction_compute_aux_config/reduction_compute_aux_config.md)（`explains`）：如何使用归约计算API 与《归约计算辅助配置接口》的实质衔接是：该指南解释 ReduceMax/Min/Sum、Repeat、DataBlock、PairElem 的粒度以及 mask/repeat 参数；基础/Reg 总览、辅助配置和 padding/count 故障直接影响选型与结果正确性。
- [Ascend950 ReduceSum AR 多行归约逐行错](../../../../../runbooks/precision/ascend950_reduce_sum_ar_multibundle_use_per_row.md)（`related`）：《Ascend950 ReduceSum AR 多行归约逐行错》说明Ascend950 上 ReduceSum<AR> 单次传入 aBundle>1 行时逐行结果错（总量近似但逐元素偏）；改逐行调用 ReduceSum(aBundle=1) 规避。仅当 aBundle>1 才触发。；《如何使用归约计算API》说明归约指令将数据集合简化为单一值或者更小的集合。按照归约操作的数据范围的不同，归约指令分为以下几种，可参考归约指令示意图：。二者在该故障专指ReduceSum AR一次处理多行时逐行错误，逐行调用、跨chunk累加和归约边界是直接修复/验证点上存在可执行的直接衔接。
- [Reduce count 必须排除 DMA 对齐填充元素](../../../../../runbooks/precision/reduction_count_excludes_dma_padding.md)（`related`）：Reduce count 必须排除 DMA 对齐填充元素 与《如何使用归约计算API》的实质衔接是：DMA 对齐容量不是 Reduce 的数学 count；DataCopyPad/padding 故障、Softmax 与 ReduceMax/Sum 各层入口共同验证填充零经 Exp 后会污染分母。
- [选择低延迟指令，优化归约操作性能](../../../../operator_practice/simd_operator_optimization/vector_compute/low_latency_instruction.md)（`related`）：如何使用归约计算API 与《选择低延迟指令，优化归约操作性能》的实质衔接是：该指南解释 ReduceMax/Min/Sum、Repeat、DataBlock、PairElem 的粒度以及 mask/repeat 参数；基础/Reg 总览、辅助配置和 padding/count 故障直接影响选型与结果正确性。
<!-- cannbot:related:end -->
