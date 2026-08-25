---
type: API
title: AscMin
description: 根据mask对源操作数src0、src1按元素求最小值，将结果写入目的操作数dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_min.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscMin

该接口根据mask，对源操作数src0、src1进行按元素求最小值操作，将结果写入目的操作数dst。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src0(输入): 源操作数（矢量数据寄存器）。；src1(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器）。用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：- mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。

- min(-0, +0) = -0。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Max/Min 逐元素非标量广播 须 Duplicate 至同长 buffer](../../../../../runbooks/precision/count_based_max_min_is_element_wise_not_scalar_broadcast.md)（`exemplifies`）：AscMin 与《Max/Min 逐元素非标量广播 须 Duplicate 至同长 buffer》的实质衔接是：AscMin 的 Reg/Vector/C++入口共享逐 lane 最小值与 mask 置零契约；scalar 变体、AscMax 对照和非标量广播故障明确操作数形态边界。
- [Min](../../../basic_api/memory_vector_compute/basic_arithmetic/min.md)（`related`）：AscMin 与《Min》的实质衔接是：AscMin 的 Reg/Vector/C++入口共享逐 lane 最小值与 mask 置零契约；scalar 变体、AscMax 对照和非标量广播故障明确操作数形态边界。
- [Min](../../../basic_api/tool_interface/numeric_limits_utils/min.md)（`related`）：AscMin 与《Min》的实质衔接是：AscMin 的 Reg/Vector/C++入口共享逐 lane 最小值与 mask 置零契约；scalar 变体、AscMax 对照和非标量广播故障明确操作数形态边界。
- [AscMax](asc_max.md)（`same_topic`）：AscMin 与《AscMax》的实质衔接是：AscMin 的 Reg/Vector/C++入口共享逐 lane 最小值与 mask 置零契约；scalar 变体、AscMax 对照和非标量广播故障明确操作数形态边界。
- [AscMin](../../vector_compute/asc_min.md)（`same_topic`）：AscMin 与《AscMin》的实质衔接是：AscMin 是两个同长 UB 向量逐元素取小；Reg/C++ 对应入口和 scalar 变体用于区分 mask/operand 形态，广播故障明确 src1 不能只给一个标量。
- [AscMinScalar](asc_min_scalar.md)（`same_topic`）：AscMinScalar 与《AscMin》的实质衔接是：AscMinScalar 在 Reg 上比较 vector 与 scalar；Vector 对应入口、tensor-tensor Min、MaxScalar 和灵活 Mins 分别界定执行层、操作数形态与相反边界。
- [Min](../../../basic_api/reg_vector_compute/basic_arithmetic/min.md)（`same_topic`）：《Min》说明根据mask对源操作数srcReg0、srcReg1按元素求最小值，将结果写入目的操作数dstReg。；《AscMin》说明根据mask对源操作数src0、src1按元素求最小值，将结果写入目的操作数dst。。二者在Reg Min与Max、标量Mins及Memory/C/SIMT等价接口的操作数形态不同，Clamp则直接组合最小/最大边界上存在可执行的直接衔接。
- [min（整数数学函数）](../../../../simt_api/math_functions/integer_math_functions/min.md)（`same_topic`）：min（整数数学函数） 与《AscMin》的实质衔接是：max 与 min、不同整数宽度/符号重载及 SIMD Min 入口直接对照 focal 模板重载的选择与边界值语义。
<!-- cannbot:related:end -->
