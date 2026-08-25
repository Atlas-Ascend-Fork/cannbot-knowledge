---
type: API
title: 归约计算
description: Memory矢量计算归约接口索引页，汇总ReduceDataBlock、ReduceRepeat、ReducePairElem及ReduceMax/Min/Sum。
tags: [task.lookup, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/reduction_compute/reduction_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 归约计算

Memory 矢量归约计算接口集合，对 LocalTensor 元素进行降维归约。ReduceMax/ReduceMin/ReduceSum 为基础归约（最大/最小/求和）；ReduceDataBlock/ReduceRepeat/ReducePairElem 提供分块、重复、成对元素的归约控制。归约结果通常写入标量或较小 Tensor，使用前需确认归约轴与数据类型支持情况。

<!-- cannbot:related:start -->
## 相关

- [int32 fp32累加reduce binary_equal不可达](../../../../../runbooks/precision/int32_fp32_reduce_binary_equal.md)（`exemplifies`）：《int32 fp32累加reduce binary_equal不可达》的任务是“int32 输入的 reduce 类算子内部 cast 到 fp32 累加，kernel 的 ReduceSum+bisection cache tree 与 golden 的 pairwise 折半是两棵不同 reduce 树；sum 超过 fp32 精确整数范围 2^24 时舍入路径不同致 1 ULP 差，cast 回 int32 后 bitwise 不一致，binary_equal 永不可达。”。《归约计算》具体提供“Memory矢量计算归约接口索引页，汇总ReduceDataBlock、ReduceRepeat、ReducePairElem及ReduceMax/Min/Sum。”，它直接用于int32→fp32 ReduceSum 的规约树、有效 count 和 2^24 舍入边界。
- [如何使用归约计算API](../../../../../guides/programming_guide/library_api/basic_api/quick_reference/how_to_use_reduction_api.md)（`explains`）：如何使用归约计算API 与《归约计算》的实质衔接是：该指南解释 ReduceMax/Min/Sum、Repeat、DataBlock、PairElem 的粒度以及 mask/repeat 参数；基础/Reg 总览、辅助配置和 padding/count 故障直接影响选型与结果正确性。
- [ReduceMin](reduce_min.md)（`same_topic`）：ReduceMin 与《归约计算》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
- [归约操作](../../../adv_api/reduction_operations/reduction_operations.md)（`same_topic`）：归约操作 与《归约计算》的实质衔接是：归约导航本身由 part_of 覆盖接口成员；这里只连接跨层归约概述/使用指南及 padding、UB、累加和多行执行等直接影响选择与验收的故障卡。
- [归约计算](../../../c_api/reg/reduce_compute/reduce_compute.md)（`same_topic`）：归约计算 与《归约计算》的实质衔接是：Reg 归约索引与 Memory 归约索引分别汇总同一 sum/max/min/datablock 能力，接口成员关系由 part_of 覆盖。
- [归约计算概述](introduction.md)（`same_topic`）：归约计算概述 与《归约计算》的实质衔接是：基础归约概述说明 pair、datablock、repeat 与全量 reduce 的粒度选择；使用指南和故障卡限定有效 count、对齐尾部、work buffer、累加类型及多行验证。
<!-- cannbot:related:end -->
