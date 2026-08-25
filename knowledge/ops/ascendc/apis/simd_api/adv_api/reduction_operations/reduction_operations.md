---
type: API
title: 归约操作
description: 归约操作接口导航页，涵盖Sum、Mean、ReduceSum、ReduceMax、ReduceMin等沿指定维度的归约计算接口。
tags: [task.lookup, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/reduction_operations.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 归约操作

Ascend C SIMD 高阶 API 归约计算导航页，提供沿指定维度对张量进行归约的 Kernel 侧接口。
涵盖基础归约（Sum、Mean）与通用归约（ReduceSum、ReduceMean、ReduceMax、ReduceMin、ReduceAny、ReduceAll、ReduceProd），以及 ReduceXorSum 按位异或求和接口。
各接口支持指定归约轴与数据类型，通常配合 Tiling 临时空间查询方法使用。

<!-- cannbot:related:start -->
## 相关

- [A5 循环内 ReduceMin 取索引致 vector core 异常](../../../../runbooks/precision/a5_reducemin_vector_core.md)（`exemplifies`）：归约操作 与《A5 循环内 ReduceMin 取索引致 vector core 异常》的实质衔接是：归约导航本身由 part_of 覆盖接口成员；这里只连接跨层归约概述/使用指南及 padding、UB、累加和多行执行等直接影响选择与验收的故障卡。
- [Ascend950 ReduceSum AR 多行归约逐行错](../../../../runbooks/precision/ascend950_reduce_sum_ar_multibundle_use_per_row.md)（`exemplifies`）：《Ascend950 ReduceSum AR 多行归约逐行错》说明Ascend950 上 ReduceSum<AR> 单次传入 aBundle>1 行时逐行结果错（总量近似但逐元素偏）；改逐行调用 ReduceSum(aBundle=1) 规避。仅当 aBundle>1 才触发。；《归约操作》说明归约操作接口导航页，涵盖Sum、Mean、ReduceSum、ReduceMax、ReduceMin等沿指定维度的归约计算接口。。二者在该故障专指ReduceSum AR一次处理多行时逐行错误，逐行调用、跨chunk累加和归约边界是直接修复/验证点上存在可执行的直接衔接。
- [Reduce work buf 额外占 UB 致 507035](../../../../runbooks/compilation/reduce_work_buf_ub_507035.md)（`exemplifies`）：归约操作 与《Reduce work buf 额外占 UB 致 507035》的实质衔接是：归约导航本身由 part_of 覆盖接口成员；这里只连接跨层归约概述/使用指南及 padding、UB、累加和多行执行等直接影响选择与验收的故障卡。
- [int32 fp32累加reduce binary_equal不可达](../../../../runbooks/precision/int32_fp32_reduce_binary_equal.md)（`exemplifies`）：《int32 fp32累加reduce binary_equal不可达》的任务是“int32 输入的 reduce 类算子内部 cast 到 fp32 累加，kernel 的 ReduceSum+bisection cache tree 与 golden 的 pairwise 折半是两棵不同 reduce 树；sum 超过 fp32 精确整数范围 2^24 时舍入路径不同致 1 ULP 差，cast 回 int32 后 bitwise 不一致，binary_equal 永不可达。”。《归约操作》具体提供“归约操作接口导航页，涵盖Sum、Mean、ReduceSum、ReduceMax、ReduceMin等沿指定维度的归约计算接口。”，它直接用于int32→fp32 ReduceSum 的规约树、有效 count 和 2^24 舍入边界。
- [如何使用归约计算API](../../../../guides/programming_guide/library_api/basic_api/quick_reference/how_to_use_reduction_api.md)（`explains`）：如何使用归约计算API 与《归约操作》的实质衔接是：该指南解释 ReduceMax/Min/Sum、Repeat、DataBlock、PairElem 的粒度以及 mask/repeat 参数；基础/Reg 总览、辅助配置和 padding/count 故障直接影响选型与结果正确性。
- [归约计算](../../basic_api/memory_vector_compute/reduction_compute/reduction_compute.md)（`same_topic`）：归约操作 与《归约计算》的实质衔接是：归约导航本身由 part_of 覆盖接口成员；这里只连接跨层归约概述/使用指南及 padding、UB、累加和多行执行等直接影响选择与验收的故障卡。
- [归约计算](../../basic_api/reg_vector_compute/reduction_compute/reduction_compute.md)（`same_topic`）：归约操作 与《归约计算》的实质衔接是：归约导航本身由 part_of 覆盖接口成员；这里只连接跨层归约概述/使用指南及 padding、UB、累加和多行执行等直接影响选择与验收的故障卡。
- [归约计算概述](../../basic_api/memory_vector_compute/reduction_compute/introduction.md)（`same_topic`）：归约计算概述 与《归约操作》的实质衔接是：基础归约概述说明 pair、datablock、repeat 与全量 reduce 的粒度选择；使用指南和故障卡限定有效 count、对齐尾部、work buffer、累加类型及多行验证。
<!-- cannbot:related:end -->
