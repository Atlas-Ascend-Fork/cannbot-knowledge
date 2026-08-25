---
type: API
title: 归约计算概述
description: 概述 Tensor 归约计算及 ReduceSum、ReduceMax、ReduceMin、ReducePairElem 等接口能力。
tags: [task.lookup, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/reduction_compute/Introduction.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Reduction计算简介

Reduction 计算接口对 tensor 数据进行规约运算，将多维数据降维。支持 ReduceSum（求和）、ReduceMax（最大值）、ReduceMin（最小值）、ReducePairElem 等模式。通过 repeatParams 配置多轮规约，支持高维切分。

<!-- cannbot:related:start -->
## 相关

- [A5 循环内 ReduceMin 取索引致 vector core 异常](../../../../../runbooks/precision/a5_reducemin_vector_core.md)（`exemplifies`）：归约计算概述 与《A5 循环内 ReduceMin 取索引致 vector core 异常》的实质衔接是：基础归约概述说明 pair、datablock、repeat 与全量 reduce 的粒度选择；使用指南和故障卡限定有效 count、对齐尾部、work buffer、累加类型及多行验证。
- [Ascend950 ReduceSum AR 多行归约逐行错](../../../../../runbooks/precision/ascend950_reduce_sum_ar_multibundle_use_per_row.md)（`exemplifies`）：《Ascend950 ReduceSum AR 多行归约逐行错》说明Ascend950 上 ReduceSum<AR> 单次传入 aBundle>1 行时逐行结果错（总量近似但逐元素偏）；改逐行调用 ReduceSum(aBundle=1) 规避。仅当 aBundle>1 才触发。；《归约计算概述》说明概述 Tensor 归约计算及 ReduceSum、ReduceMax、ReduceMin、ReducePairElem 等接口能力。。二者在该故障专指ReduceSum AR一次处理多行时逐行错误，逐行调用、跨chunk累加和归约边界是直接修复/验证点上存在可执行的直接衔接。
- [DataCopyPad 未填满强制对齐缓冲 — 小维规约读入脏尾部](../../../../../runbooks/precision/datacopypad_tail_must_initialize_full_reduction_extent.md)（`exemplifies`）：归约计算概述 与《DataCopyPad 未填满强制对齐缓冲 — 小维规约读入脏尾部》的实质衔接是：基础归约概述说明 pair、datablock、repeat 与全量 reduce 的粒度选择；使用指南和故障卡限定有效 count、对齐尾部、work buffer、累加类型及多行验证。
- [Reduce work buf 额外占 UB 致 507035](../../../../../runbooks/compilation/reduce_work_buf_ub_507035.md)（`exemplifies`）：归约计算概述 与《Reduce work buf 额外占 UB 致 507035》的实质衔接是：基础归约概述说明 pair、datablock、repeat 与全量 reduce 的粒度选择；使用指南和故障卡限定有效 count、对齐尾部、work buffer、累加类型及多行验证。
- [int32 fp32累加reduce binary_equal不可达](../../../../../runbooks/precision/int32_fp32_reduce_binary_equal.md)（`exemplifies`）：《int32 fp32累加reduce binary_equal不可达》的任务是“int32 输入的 reduce 类算子内部 cast 到 fp32 累加，kernel 的 ReduceSum+bisection cache tree 与 golden 的 pairwise 折半是两棵不同 reduce 树；sum 超过 fp32 精确整数范围 2^24 时舍入路径不同致 1 ULP 差，cast 回 int32 后 bitwise 不一致，binary_equal 永不可达。”。《归约计算概述》具体提供“概述 Tensor 归约计算及 ReduceSum、ReduceMax、ReduceMin、ReducePairElem 等接口能力。”，它直接用于int32→fp32 ReduceSum 的规约树、有效 count 和 2^24 舍入边界。
- [如何使用归约计算API](../../../../../guides/programming_guide/library_api/basic_api/quick_reference/how_to_use_reduction_api.md)（`explains`）：如何使用归约计算API 与《归约计算概述》的实质衔接是：该指南解释 ReduceMax/Min/Sum、Repeat、DataBlock、PairElem 的粒度以及 mask/repeat 参数；基础/Reg 总览、辅助配置和 padding/count 故障直接影响选型与结果正确性。
- [GetReduceRepeatSumSpr](../reduction_compute_aux_config/get_reduce_repeat_sum_spr_isasi.md)（`related`）：GetReduceRepeatSumSpr 与《归约计算概述》的实质衔接是：GetReduceRepeatSumSpr 只读取前 n 连续 ReduceSum 的全局结果；ReduceSum 调用、临时空间和逐行/多 bundle 归约故障直接约束其使用。
- [ReduceMin](reduce_min.md)（`same_topic`）：ReduceMin 与《归约计算概述》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
- [归约操作](../../../adv_api/reduction_operations/reduction_operations.md)（`same_topic`）：归约计算概述 与《归约操作》的实质衔接是：基础归约概述说明 pair、datablock、repeat 与全量 reduce 的粒度选择；使用指南和故障卡限定有效 count、对齐尾部、work buffer、累加类型及多行验证。
- [归约计算](reduction_compute.md)（`same_topic`）：归约计算概述 与《归约计算》的实质衔接是：基础归约概述说明 pair、datablock、repeat 与全量 reduce 的粒度选择；使用指南和故障卡限定有效 count、对齐尾部、work buffer、累加类型及多行验证。
- [归约计算](../../reg_vector_compute/reduction_compute/reduction_compute.md)（`same_topic`）：归约计算概述 与《归约计算》的实质衔接是：基础归约概述说明 pair、datablock、repeat 与全量 reduce 的粒度选择；使用指南和故障卡限定有效 count、对齐尾部、work buffer、累加类型及多行验证。
<!-- cannbot:related:end -->
