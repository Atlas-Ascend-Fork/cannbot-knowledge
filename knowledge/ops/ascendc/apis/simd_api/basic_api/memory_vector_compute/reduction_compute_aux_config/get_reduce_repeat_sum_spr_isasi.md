---
type: API
title: GetReduceRepeatSumSpr
description: 获取ReduceSum接口前n个数据连续计算的结果，以全局变量形式存储。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/reduction_compute_aux_config/GetReduceRepeatSumSpr_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetReduceRepeatSumSpr

获取ReduceSum接口前n个数据连续计算的结果，以全局变量形式存储。

ReduceSum接口对所有输入数据进行求和，计算过程如下。 图1 ReduceSum计算示意图

本接口组包含 ReduceSum。

本接口属于 UB 矢量计算归约接口。

约束：源操作数及sharedTmpBuffer的地址对齐约束请参考通用地址对齐约束，起始地址需要32字节对齐；目的操作数的起始地址对齐约束请参考ReduceRepeat-表3。；操作数地址重叠约束请参考通用地址重叠约束。；需要使用sharedTmpBuffer的情况下，支持dst与sharedTmpBuffer地址重叠（通常情况下dst比sharedTmpBuffer所需的空间要小），此时sharedTmpBuffer必须满足所需空间要求，详情请参考关键特性说明。；当参数count或repeatTime取值为0时，该接口的行为如下：

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 ReduceSum AR 多行归约逐行错](../../../../../runbooks/precision/ascend950_reduce_sum_ar_multibundle_use_per_row.md)（`exemplifies`）：《Ascend950 ReduceSum AR 多行归约逐行错》说明Ascend950 上 ReduceSum<AR> 单次传入 aBundle>1 行时逐行结果错（总量近似但逐元素偏）；改逐行调用 ReduceSum(aBundle=1) 规避。仅当 aBundle>1 才触发。；《GetReduceRepeatSumSpr》说明获取ReduceSum接口前n个数据连续计算的结果，以全局变量形式存储。。二者在该故障专指ReduceSum AR一次处理多行时逐行错误，逐行调用、跨chunk累加和归约边界是直接修复/验证点上存在可执行的直接衔接。
- [AscRepeatReduceSum](../../../c_api/vector_compute/asc_repeat_reduce_sum.md)（`related`）：GetReduceRepeatSumSpr 与《AscRepeatReduceSum》的实质衔接是：GetReduceRepeatSumSpr 只读取前 n 连续 ReduceSum 的全局结果；ReduceSum 调用、临时空间和逐行/多 bundle 归约故障直接约束其使用。
- [GetReduceSumMaxMinTmpSize](../../../adv_api/reduction_operations/reduce_sum_interface/get_reduce_sum_max_min_tmp_size.md)（`related`）：GetReduceRepeatSumSpr 与《GetReduceSumMaxMinTmpSize》的实质衔接是：GetReduceRepeatSumSpr 只读取前 n 连续 ReduceSum 的全局结果；ReduceSum 调用、临时空间和逐行/多 bundle 归约故障直接约束其使用。
- [ReduceRepeat](../reduction_compute/reduce_repeat.md)（`related`）：读取 Sum SPR 可核对 ReduceRepeat 的分 repeat 结果。
- [ReduceSum](../../../adv_api/reduction_operations/reduce_sum_interface/reduce_sum.md)（`related`）：GetReduceRepeatSumSpr 与《ReduceSum》的实质衔接是：GetReduceRepeatSumSpr 只读取前 n 连续 ReduceSum 的全局结果；ReduceSum 调用、临时空间和逐行/多 bundle 归约故障直接约束其使用。
- [ReduceSum](../reduction_compute/reduce_sum.md)（`related`）：GetReduceRepeatSumSpr 与《ReduceSum》的实质衔接是：GetReduceRepeatSumSpr 只读取前 n 连续 ReduceSum 的全局结果；ReduceSum 调用、临时空间和逐行/多 bundle 归约故障直接约束其使用。
- [ReduceSum接口](../../../adv_api/reduction_operations/reduce_sum_interface/reduce_sum_interface.md)（`related`）：GetReduceRepeatSumSpr 与《ReduceSum接口》的实质衔接是：GetReduceRepeatSumSpr 只读取前 n 连续 ReduceSum 的全局结果；ReduceSum 调用、临时空间和逐行/多 bundle 归约故障直接约束其使用。
- [归约计算概述](../reduction_compute/introduction.md)（`related`）：GetReduceRepeatSumSpr 与《归约计算概述》的实质衔接是：GetReduceRepeatSumSpr 只读取前 n 连续 ReduceSum 的全局结果；ReduceSum 调用、临时空间和逐行/多 bundle 归约故障直接约束其使用。
- [归约计算辅助配置接口](reduction_compute_aux_config.md)（`related`）：GetReduceRepeatSumSpr 与《归约计算辅助配置接口》的实质衔接是：GetReduceRepeatSumSpr 只读取前 n 连续 ReduceSum 的全局结果；ReduceSum 调用、临时空间和逐行/多 bundle 归约故障直接约束其使用。
- [GetReduceRepeatMaxMinSpr](get_reduce_repeat_max_min_spr_isasi.md)（`same_topic`）：GetReduceRepeatMaxMinSpr 的核心契约是“获取ReduceRepeat或ReduceMax/ReduceMin计算的最值及索引，结果以全局变量形式存储”；GetReduceRepeatSumSpr 补充“获取ReduceSum接口前n个数据连续计算的结果，以全局变量形式存储”。
<!-- cannbot:related:end -->
