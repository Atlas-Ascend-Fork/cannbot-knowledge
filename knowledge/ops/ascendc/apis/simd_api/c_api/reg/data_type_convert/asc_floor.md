---
type: API
title: AscFloor
description: 将src中的浮点数元素按照FLOOR（向负无穷方向舍入）舍入模式截断到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_floor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscFloor

将src中的浮点数元素按照FLOOR（向负无穷方向舍入）舍入模式截断到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。

关于舍入模式

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half。

约束：float类型只支持不饱和模式。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [舍入模式与饱和模式](rounding_mode.md)（`related`）：AscFloor说明将src中的浮点数元素按照FLOOR（向负无穷方向舍入）舍入模式截断到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。
- [AscFloat2Int16](asc_float2int16.md)（`same_topic`）：《AscFloat2Int16》处理“将float类型数据转化为int16_t类型，并支持多种舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式与饱和模式。 由于源操作数与目的操作数类型位宽比为2:1，写入数据时需要将一个VL大小的数据分为两部分，根据不同接口选择数据写入索引为奇数的位置或偶数的位置。”。《AscFloor》明确提供“将src中的浮点数元素按照FLOOR（向负无穷方向舍入）舍入模式截断到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。”，其参数、调用或验证步骤直接接入float 到 int16 的同源同目标转换及 rounding/saturation 选择。
- [AscFloat2float](../../vector_compute/asc_float2float.md)（`same_topic`）：AscFloat2float 与《AscFloor》的实质衔接是：AscFloat2float 通过舍入模式规范同类型值；SIMT 同名转换和 Rint/Round/Floor/Ceil/Trunc 卡提供每种模式的确切数学定义。
- [Floor](../../../adv_api/math_compute/floor_interface/floor.md)（`same_topic`）：《AscFloor》处理“将src中的浮点数元素按照FLOOR（向负无穷方向舍入）舍入模式截断到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。”。《Floor》提供“获取小于或等于x的最小整数值，即向负无穷取整”，其具体合同或探针直接接入Floor 的 Reg/Memory/高级/SIMT 等价运算语义。
- [Floorf](../../../../simt_api/math_functions/float_math_functions/floorf.md)（`same_topic`）：《Floorf》处理“获取小于或等于输入数据的最大整数值。”。《AscFloor》明确“将src中的浮点数元素按照FLOOR（向负无穷方向舍入）舍入模式截断到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。”，可直接用于核对float floor 与 half/half2、Reg/C API、高阶接口的同一向负无穷取整语义。
- [Floor接口](../../../adv_api/math_compute/floor_interface/floor_interface.md)（`same_topic`）：《AscFloor》处理“将src中的浮点数元素按照FLOOR（向负无穷方向舍入）舍入模式截断到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。”。《Floor接口》提供“按元素向负无穷取整，并提供临时空间大小获取接口。”，其具体合同或探针直接接入Floor 的 Reg/Memory/高级/SIMT 等价运算语义。
- [H2Floor](../../../../simt_api/math_functions/bfloat16_type/bfloat16x2_math_functions/h2floor.md)（`same_topic`）：《H2Floor》处理“获取小于或等于输入数据各元素的最大整数值。”。《AscFloor》提供“将src中的浮点数元素按照FLOOR（向负无穷方向舍入）舍入模式截断到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。”，其具体合同或探针直接接入packed floor 与 scalar/Memory/高级接口的同一向负无穷取整语义。
- [H2Floor](../../../../simt_api/math_functions/half_type/half2_math_functions/h2floor.md)（`same_topic`）：《AscFloor》处理“将src中的浮点数元素按照FLOOR（向负无穷方向舍入）舍入模式截断到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。”。《H2Floor》提供“获取小于或等于输入数据各元素的最大整数值。”，其具体合同或探针直接接入Floor 的 Reg/Memory/高级/SIMT 等价运算语义。
- [Hfloor](../../../../simt_api/math_functions/bfloat16_type/bfloat16_math_functions/hfloor.md)（`same_topic`）：《AscFloor》处理“将src中的浮点数元素按照FLOOR（向负无穷方向舍入）舍入模式截断到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。”。《Hfloor》提供“获取小于或等于输入bfloat16_t数据的最大整数值。”，其具体合同或探针直接接入Floor 的 Reg/Memory/高级/SIMT 等价运算语义。
- [Hfloor](../../../../simt_api/math_functions/half_type/half_math_functions/hfloor.md)（`same_topic`）：《Hfloor》处理“获取小于或等于输入half数据的最大整数值。”。《AscFloor》明确“将src中的浮点数元素按照FLOOR（向负无穷方向舍入）舍入模式截断到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。”，可直接用于核对half floor 与 float/half2、Reg/C API、高阶接口的同一取整语义。
<!-- cannbot:related:end -->
