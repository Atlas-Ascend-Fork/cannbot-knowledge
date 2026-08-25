---
type: API
title: Truncate
description: 将源操作数的浮点数元素截断到整数位，保持原数据类型不变，支持多种舍入模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/type_conversion/Truncate_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Truncate

将源操作数的浮点数元素截断到整数位，保持原数据类型不变，支持多种舍入模式。

将源操作数的浮点数元素截断到整数位，同时源操作数的数据类型保持不变。

本接口属于 UB 矢量计算类型转换接口。

参数说明：T：操作数数据类型。；roundMode：舍入模式，取值如下。 **RoundMode::CAST_RINT**：返回最接近的整数，若存在两个同样接近的整数，则选择偶数。 **RoundMode::CAST_ROUND**：四舍五入取整。 **RoundMode::CAST_FLOOR**：向下取整。 **RoundMode::CAST_CEIL**：向上取整。 **RoundMode::CAST_TRUNC**：截断取整（直接舍弃小数部分）。；dst：输出 目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 LocalTensor的起始地址需要32字节对齐。；src：输入 源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 LocalTensor的起始地址需要32字节对齐。 源操作数的数据类型需要与目的操作数保持一致。；count：输入 参与计算的元素个数。

约束：操作数地址对齐要求请参见通用地址对齐约束。；针对Ascend 950PR/Ascend 950DT，该接口通过VF调用Reg矢量计算API实现兼容，当参数count取值为0时，不保证该接口被视为NOP（空操作）。

<!-- cannbot:related:start -->
## 相关

- [Cast](../../reg_vector_compute/type_conversion/cast.md)（`related`）：《Truncate》处理“将源操作数的浮点数元素截断到整数位，保持原数据类型不变，支持多种舍入模式。”。《Cast》明确“Reg矢量计算的精度转换接口，支持浮点转整数、浮点转浮点、整数转浮点和整数转整数四种类型转换。”，可直接用于核对Truncate 向零取整在 Cast round-mode、高阶/基础/SIMT 接口中的等价语义。
- [RoundMode](../../reg_vector_compute/aux_data_types/round_mode.md)（`related`）：《Truncate》处理“将源操作数的浮点数元素截断到整数位，保持原数据类型不变，支持多种舍入模式。”。《RoundMode》明确“枚举类型，用于设置精度转换时的舍入模式，支持向偶数舍入、向下、向上、四舍五入、截断等多种模式。”，可直接用于核对Truncate 向零取整在 Cast round-mode、高阶/基础/SIMT 接口中的等价语义。
- [Truncate](../../reg_vector_compute/type_conversion/truncate.md)（`related`）：Memory Vector Truncate 对 LocalTensor 执行相同舍入到整数值且保留浮点类型的操作，数据通路不同。
- [__float2float_rz](../../../../simt_api/math_functions/data_type_conversion/type_conversion_functions/_float2float_rz.md)（`related`）：《Truncate》处理“将源操作数的浮点数元素截断到整数位，保持原数据类型不变，支持多种舍入模式。”。《__float2float_rz》明确“将浮点数四舍五入取整，并遵循CAST_TRUNC模式。”，可直接用于核对Truncate 向零取整在 Cast round-mode、高阶/基础/SIMT 接口中的等价语义。
- [__float2int_rz](../../../../simt_api/math_functions/data_type_conversion/type_conversion_functions/_float2int_rz.md)（`related`）：__float2int_rz 与《Truncate》的实质衔接是：__float2int_rz 按 CAST_TRUNC 把 float 饱和到 int32；RN/RNA/RD/RU、转换总览、AscFloat2int32 与 Cast/Truncate 映射同一模式。
- [H2Trunc](../../../../simt_api/math_functions/bfloat16_type/bfloat16x2_math_functions/h2trunc.md)（`same_topic`）：《Truncate》处理“将源操作数的浮点数元素截断到整数位，保持原数据类型不变，支持多种舍入模式。”。《H2Trunc》明确“获取对输入数据各元素的浮点数截断后的整数。”，可直接用于核对Truncate 向零取整在 Cast round-mode、高阶/基础/SIMT 接口中的等价语义。
- [H2Trunc](../../../../simt_api/math_functions/half_type/half2_math_functions/h2trunc.md)（`same_topic`）：《Truncate》处理“将源操作数的浮点数元素截断到整数位，保持原数据类型不变，支持多种舍入模式。”。《H2Trunc》明确“获取对输入数据各元素的浮点数截断后的整数。”，可直接用于核对Truncate 向零取整在 Cast round-mode、高阶/基础/SIMT 接口中的等价语义。
- [Htrunc](../../../../simt_api/math_functions/bfloat16_type/bfloat16_math_functions/htrunc.md)（`same_topic`）：《Truncate》处理“将源操作数的浮点数元素截断到整数位，保持原数据类型不变，支持多种舍入模式。”。《Htrunc》明确“获取对输入bfloat16_t数据浮点数截断后的整数。”，可直接用于核对Truncate 向零取整在 Cast round-mode、高阶/基础/SIMT 接口中的等价语义。
- [Htrunc](../../../../simt_api/math_functions/half_type/half_math_functions/htrunc.md)（`same_topic`）：《Truncate》处理“将源操作数的浮点数元素截断到整数位，保持原数据类型不变，支持多种舍入模式。”。《Htrunc》明确“获取对输入half数据浮点数截断后的整数。”，可直接用于核对Truncate 向零取整在 Cast round-mode、高阶/基础/SIMT 接口中的等价语义。
- [Trunc](../../../adv_api/math_compute/trunc_interface/trunc.md)（`same_topic`）：《Truncate》处理“将源操作数的浮点数元素截断到整数位，保持原数据类型不变，支持多种舍入模式。”。《Trunc》明确“按元素做浮点数截断，即向零取整操作。”，可直接用于核对Truncate 向零取整在 Cast round-mode、高阶/基础/SIMT 接口中的等价语义。
- [Truncf](../../../../simt_api/math_functions/float_math_functions/truncf.md)（`same_topic`）：《Truncate》处理“将源操作数的浮点数元素截断到整数位，保持原数据类型不变，支持多种舍入模式。”。《Truncf》明确“获取对输入数据的浮点数截断后的整数。”，可直接用于核对Truncate 向零取整在 Cast round-mode、高阶/基础/SIMT 接口中的等价语义。
- [Trunc接口](../../../adv_api/math_compute/trunc_interface/trunc_interface.md)（`same_topic`）：《Truncate》处理“将源操作数的浮点数元素截断到整数位，保持原数据类型不变，支持多种舍入模式。”。《Trunc接口》明确“按元素做浮点数截断（向零取整），并提供临时空间大小获取接口。”，可直接用于核对Truncate 向零取整在 Cast round-mode、高阶/基础/SIMT 接口中的等价语义。
<!-- cannbot:related:end -->
