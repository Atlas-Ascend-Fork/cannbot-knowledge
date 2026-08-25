---
type: API
title: AscCeil
description: 将src中的浮点数元素按照CEIL（向正无穷方向舍入）舍入模式截断到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_ceil.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscCeil

将src中的浮点数元素按照CEIL（向正无穷方向舍入）舍入模式截断到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。

关于舍入模式

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half。

约束：float类型只支持不饱和模式。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscFloat2Int16](asc_float2int16.md)（`related`）：《AscFloat2Int16》处理“将float类型数据转化为int16_t类型，并支持多种舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式与饱和模式。 由于源操作数与目的操作数类型位宽比为2:1，写入数据时需要将一个VL大小的数据分为两部分，根据不同接口选择数据写入索引为奇数的位置或偶数的位置。”。《AscCeil》明确提供“将src中的浮点数元素按照CEIL（向正无穷方向舍入）舍入模式截断到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。”，其参数、调用或验证步骤直接接入float 到 int16 的同源同目标转换及 rounding/saturation 选择。
- [Ceil](../../../adv_api/math_compute/ceil_interface/ceil.md)（`related`）：Ceil 与《AscCeil》的实质衔接是：Ceil kernel 依赖两种临时空间查询，C API 是对应入口，Floor 提供相反取整边界；多核尾块卡直接验证 remaining 计数错误。
- [GetCeilTmpBufferFactorSize](../../../adv_api/math_compute/ceil_interface/get_ceil_tmp_buffer_factor_size.md)（`related`）：GetCeilTmpBufferFactorSize 与《AscCeil》的实质衔接是：factor 查询与 GetCeilMaxMinTmpSize 共同换算 Ceil 单次元素数，Ceil/C API 是消费端；tmpBuffer 步长故障直接验证空间公式错误会造成 UB 越界。
- [Ceilf](../../../../simt_api/math_functions/float_math_functions/ceilf.md)（`same_topic`）：AscCeil 将向正无穷取整映射到带 mask 的 Reg C API，结果仍保持浮点类型，与标量 ceilf 语义一致。
<!-- cannbot:related:end -->
