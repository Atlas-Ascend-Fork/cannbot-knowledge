---
type: API
title: Cast
description: 根据源操作数和目的操作数的数据类型进行精度转换，支持多种舍入模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/type_conversion/Cast.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Cast

类型转换接口，将源 tensor 数据转换为目标数据类型。支持多种舍入模式（ROUND、FLOOR、CEIL、CAST_RINT 等）和数据类型组合。头文件 `basic_api/kernel_operator_vec_intf.h`。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [BF16 gamma Cast 分阶段编排导致随机 NaN](../../../../../runbooks/precision/bf16_gamma_cast_must_share_ordered_compute_stage.md)（`exemplifies`）：本卡明确用 AscendC::Cast 完成 gamma/x BF16→FP32 与输出窄化；Cast API给出类型转换和舍入契约。
- [特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换](../../../../../runbooks/precision/b16_reg_cast_layout_should_convert_at_localtensor_boundary.md)（`exemplifies`）：该故障卡的可执行修复正是把转换移到 LocalTensor 边界并调用 Memory《Cast》，以此建立 B16↔FP32 正确性基线。
- [__float2int_rn](../../../../simt_api/math_functions/data_type_conversion/type_conversion_functions/_float2int_rn.md)（`related`）：__float2int_rn 与《Cast》的实质衔接是：__float2int_rn 与 RNA/RD/RU/RZ 共享 float→int32 契约；类型转换总览和 AscFloat2int32/Cast 映射出对应舍入模式与溢出边界。
- [__float2int_rz](../../../../simt_api/math_functions/data_type_conversion/type_conversion_functions/_float2int_rz.md)（`related`）：__float2int_rz 与《Cast》的实质衔接是：__float2int_rz 按 CAST_TRUNC 把 float 饱和到 int32；RN/RNA/RD/RU、转换总览、AscFloat2int32 与 Cast/Truncate 映射同一模式。
- [数据类型转换概述](../../../../simt_api/math_functions/data_type_conversion/overview.md)（`related`）：SIMT 转换概述明确隐式/显式转换、舍入和饱和模式对结果的影响，可帮助把矢量 Cast 的 mode 选择映射到逐线程标量实现。
- [类型转换](type_conversion.md)（`related`）：Cast 在源/目的 dtype 间转换精度并按 RoundMode 舍入，是需要改变数据类型时的具体入口。
- [Cast](../../reg_vector_compute/type_conversion/cast.md)（`same_topic`）：《Cast》说明Reg矢量计算的精度转换接口，支持浮点转整数、浮点转浮点、整数转浮点和整数转整数四种类型转换。；《Cast》说明根据源操作数和目的操作数的数据类型进行精度转换，支持多种舍入模式。。二者在Reg Cast的源目类型布局、舍入、饱和及mask trait必须共同匹配，相关编译和NaN故障是这些配置错误的直接验证上存在可执行的直接衔接。
- [类型转换辅助配置接口](../type_conversion_aux_config/type_conversion_aux_config.md)（`same_topic`）：类型转换辅助配置接口 与《Cast》的实质衔接是：类型转换辅助配置以 deq scale/rounding 驱动 Cast/Truncate 与精度转换。
<!-- cannbot:related:end -->
