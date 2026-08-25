---
type: API
title: Truncate
description: 将源操作数中的浮点数元素截断为整数值并保留原数据类型，存入目的操作数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/type_conversion/Truncate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Truncate

将源操作数中的浮点数元素截断为整数值（保留原数据类型），并存入目的操作数。

头文件："basic_api/reg_compute/kernel_reg_compute_vec_vconv_intf.h"。

参数：T: 操作数数据类型。支持的数据类型请参考数据类型。；roundMode: 舍入模式，取值如下： • RoundMode::CAST_RINT • RoundMode::CAST_ROUND • RoundMode::CAST_FLOOR • RoundMode::CAST_CEIL • RoundMode::CAST_TRUNC；mode: MaskMergeMode枚举类型，选择MERGING模式或ZEROING模式。 • ZEROING模式下，mask未筛选的元素在dstReg中置零。 • MERGING模式当前不支持。；S: srcReg/dstReg类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg(输入): 源操作数。 类型为RegTensor；mask(输入): 源操作数元素操作的有效指示，详细说明请参考MaskReg。

支持数据类型：half、bfloat16_t、float。

约束：- float类型只支持不饱和模式。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Cast](cast.md)（`related`）：《Cast》说明Reg矢量计算的精度转换接口，支持浮点转整数、浮点转浮点、整数转浮点和整数转整数四种类型转换。；《Truncate》说明将源操作数中的浮点数元素截断为整数值并保留原数据类型，存入目的操作数。。二者在Reg Cast的源目类型布局、舍入、饱和及mask trait必须共同匹配，相关编译和NaN故障是这些配置错误的直接验证上存在可执行的直接衔接。
- [RoundMode](../aux_data_types/round_mode.md)（`related`）：RoundMode 定义 Truncate 的五种舍入行为，直接决定半整数与负数的结果。
- [Trunc](../../../adv_api/math_compute/trunc_interface/trunc.md)（`related`）：Advanced Trunc 固定向零截断，而 Reg Truncate 可选择 RINT、ROUND、FLOOR、CEIL 或 TRUNC。
- [Truncate](../../memory_vector_compute/type_conversion/truncate_isasi.md)（`related`）：Memory Vector Truncate 对 LocalTensor 执行相同舍入到整数值且保留浮点类型的操作，数据通路不同。
- [H2Trunc](../../../../simt_api/math_functions/half_type/half2_math_functions/h2trunc.md)（`same_topic`）：H2Trunc 与《Truncate》的实质衔接是：这些接口执行向零取整或与之紧邻的 floor/rint 舍入；half2、bfloat16x2、标量、SIMD 与 C 版本用于在数据宽度和执行层变化时保持 trunc 语义。
- [Truncf](../../../../simt_api/math_functions/float_math_functions/truncf.md)（`same_topic`）：Truncf 与《Truncate》的实质衔接是：Truncf 与 SIMD、基础、C、half/half2/bfloat16x2 Trunc 都实现向零截断；空间查询只适用于高阶 tensor 版本，不能套到标量入口。
<!-- cannbot:related:end -->
