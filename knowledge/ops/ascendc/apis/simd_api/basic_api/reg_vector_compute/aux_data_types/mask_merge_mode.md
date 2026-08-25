---
type: API
title: MaskMergeMode
description: 枚举类型，用于指定寄存器数据写入模式，包括ZEROING置零和MERGING保留原值两种模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/aux_data_types/MaskMergeMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# MaskMergeMode

枚举类型，用于指定寄存器数据写入模式，包括ZEROING置零和MERGING保留原值两种模式。

本接口属于 Reg 矢量计算辅助数据类型定义。

# MaskMergeMode | 参数名 | 描述 | | :-- | :-- | | MaskMergeMode | 用于指定写入寄存器数据模式。 enum class MaskMergeMode { UNKNOWN, MERGING, ZEROING }; • UNKNOWN：当转换类型不支持MaskMergeMode时，选择该模式； • ZEROING：mask未选择的元素在dst中置零； • MERGING：mask未选择的元素对应dst元素中保留dst原值。 | 以Duplicate接口为例，ZEROING和MERGING模式图示如下： 图1 ZEROING/MERGING对比

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Duplicate 广播枚举与模板顺序不兼容](../../../../../runbooks/compilation/reg_duplicate_highlow_precedes_merge_mode.md)（`exemplifies`）：MaskMergeMode 与《Duplicate 广播枚举与模板顺序不兼容》的实质衔接是：MaskMergeMode 决定 inactive lane 合并行为；支持矩阵和两张编译故障卡直接约束枚举选择与模板实参顺序。
- [Reg Cast 默认 UNKNOWN mask 被拒 — 显式 ZEROING](../../../../../runbooks/compilation/reg_cast_requires_explicit_zeroing_trait.md)（`exemplifies`）：MaskMergeMode 与《Reg Cast 默认 UNKNOWN mask 被拒 — 显式 ZEROING》的实质衔接是：MaskMergeMode 决定 inactive lane 合并行为；支持矩阵和两张编译故障卡直接约束枚举选择与模板实参顺序。
- [Reg CastTrait RoundMode 命名空间编译失败](../../../../../runbooks/compilation/casttrait_roundmode_is_in_ascendc.md)（`exemplifies`）：Reg CastTrait RoundMode 命名空间编译失败 与《MaskMergeMode》的实质衔接是：该故障由 CastTrait 字段 RoundMode 的错误命名空间触发；trait 存储期/NTTP、merge/sat/round 枚举和 Cast 模式故障共同约束真实模板声明。
- [Reg 尾块 masked Add 清零跨块累加器](../../../../../runbooks/precision/reg_tail_mask_zeroing_clears_cross_chunk_accumulator.md)（`exemplifies`）：《MaskMergeMode》给出本故障的核心硬件语义：ZEROING 清零未选 lane，MERGING 保留目标值，正好解释 tail Add 为什么破坏历史累加。
- [Reg矢量计算编程（C++ Tensor编程）](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/reg_vector_computation.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《MaskMergeMode》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [Cast](../type_conversion/cast.md)（`related`）：《Cast》说明Reg矢量计算的精度转换接口，支持浮点转整数、浮点转浮点、整数转浮点和整数转整数四种类型转换。；《MaskMergeMode》说明枚举类型，用于指定寄存器数据写入模式，包括ZEROING置零和MERGING保留原值两种模式。。二者在Reg Cast的源目类型布局、舍入、饱和及mask trait必须共同匹配，相关编译和NaN故障是这些配置错误的直接验证上存在可执行的直接衔接。
- [MaskReg](../register_data_types/mask_reg.md)（`related`）：MaskReg 与《MaskMergeMode》的实质衔接是：MaskReg 定义有效 lane，直接被 Load/Store、MaskGen 与 MaskReg 计算消费；C 创建/更新接口、merge mode、复用指南和两个编译故障明确其构造约束。
- [Mul](../basic_arithmetic/mul.md)（`related`）：Mul 与《MaskMergeMode》的实质衔接是：Reg Mul 的 masked 写入受 MaskMergeMode 控制；Memory Mul、Reg C API AscMul 和 Vector C API AscMul 执行同一逐元素乘法，但操作数位置、执行层与掩码接口不同。
- [Reg矢量计算接口MergeMode支持情况汇总](../../../../appendix/reg_vector_compute_interface_mergemode_support_summary.md)（`related`）：MaskMergeMode 与《Reg矢量计算接口MergeMode支持情况汇总》的实质衔接是：MaskMergeMode 决定 inactive lane 合并行为；支持矩阵和两张编译故障卡直接约束枚举选择与模板实参顺序。
- [AscCreateMask](../../../c_api/reg/reg_data_types/asc_create_mask.md)（`same_topic`）：AscCreateMask 与《MaskMergeMode》的实质衔接是：AscCreateMask 根据数据位宽和 pat_mode 生成 MaskReg，随后由 UpdateMask/GetMaskSpr、Load/Store 和 MergeMode 消费；两个编译错例限定模板类型与可写引用。
- [Move](../reg_data_load/move.md)（`same_topic`）：Move 与《MaskMergeMode》的实质衔接是：Move 的掩码写入语义由 C API 对应接口、MaskMergeMode 和 MaskReg 计算契约共同界定。
<!-- cannbot:related:end -->
