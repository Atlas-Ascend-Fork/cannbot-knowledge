---
type: API
title: Floorf
description: 获取小于或等于输入数据的最大整数值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/floorf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Floorf

功能：获取小于或等于输入数据的最大整数值。

函数原型：float floorf(float x)

参数：x（输入）源操作数。

返回值：小于或等于输入数据的最大整数值。特殊值：nan→nan；inf→inf；-inf→-inf。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [AscFloor](../../../simd_api/c_api/reg/data_type_convert/asc_floor.md)（`same_topic`）：《Floorf》处理“获取小于或等于输入数据的最大整数值。”。《AscFloor》明确“将src中的浮点数元素按照FLOOR（向负无穷方向舍入）舍入模式截断到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。”，可直接用于核对float floor 与 half/half2、Reg/C API、高阶接口的同一向负无穷取整语义。
- [Floor](../../../simd_api/adv_api/math_compute/floor_interface/floor.md)（`same_topic`）：《Floorf》处理“获取小于或等于输入数据的最大整数值。”。《Floor》明确“获取小于或等于x的最小整数值，即向负无穷取整”，可直接用于核对float floor 与 half/half2、Reg/C API、高阶接口的同一向负无穷取整语义。
- [Floor接口](../../../simd_api/adv_api/math_compute/floor_interface/floor_interface.md)（`same_topic`）：《Floorf》处理“获取小于或等于输入数据的最大整数值。”。《Floor接口》明确“按元素向负无穷取整，并提供临时空间大小获取接口。”，可直接用于核对float floor 与 half/half2、Reg/C API、高阶接口的同一向负无穷取整语义。
- [H2Floor](../bfloat16_type/bfloat16x2_math_functions/h2floor.md)（`same_topic`）：《Floorf》处理“获取小于或等于输入数据的最大整数值。”。《H2Floor》明确“获取小于或等于输入数据各元素的最大整数值。”，可直接用于核对float floor 与 half/half2、Reg/C API、高阶接口的同一向负无穷取整语义。
- [H2Floor](../half_type/half2_math_functions/h2floor.md)（`same_topic`）：《Floorf》处理“获取小于或等于输入数据的最大整数值。”。《H2Floor》明确“获取小于或等于输入数据各元素的最大整数值。”，可直接用于核对float floor 与 half/half2、Reg/C API、高阶接口的同一向负无穷取整语义。
- [Hfloor](../bfloat16_type/bfloat16_math_functions/hfloor.md)（`same_topic`）：《Floorf》处理“获取小于或等于输入数据的最大整数值。”。《Hfloor》明确“获取小于或等于输入bfloat16_t数据的最大整数值。”，可直接用于核对float floor 与 half/half2、Reg/C API、高阶接口的同一向负无穷取整语义。
- [Hfloor](../half_type/half_math_functions/hfloor.md)（`same_topic`）：《Floorf》处理“获取小于或等于输入数据的最大整数值。”。《Hfloor》明确“获取小于或等于输入half数据的最大整数值。”，可直接用于核对float floor 与 half/half2、Reg/C API、高阶接口的同一向负无穷取整语义。
<!-- cannbot:related:end -->
