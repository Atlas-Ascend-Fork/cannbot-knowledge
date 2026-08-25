---
type: API
title: H2Floor
description: 获取小于或等于输入数据各元素的最大整数值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_math_functions/h2floor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# H2Floor

功能：获取小于或等于输入数据各元素的最大整数值。

函数原型：bfloat16x2_t h2floor(bfloat16x2_t x)

参数：x（输入）源操作数。

返回值：小于或等于输入数据各元素的最大整数值。本接口受全局饱和模式影响，。特殊值：0→0；-0→-0；nan→0；inf→ASCRT_MAX_NORMAL_BF16；-inf→-ASCRT_MAX_NORMAL_BF16。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Rint](h2rint.md)（`related`）：H2Floor 与 H2Rint 处理相同 packed BF16x2，但按向负无穷取整；负数和半整数结果需按 oracle 选型。
- [AscFloor](../../../../simd_api/c_api/reg/data_type_convert/asc_floor.md)（`same_topic`）：《H2Floor》处理“获取小于或等于输入数据各元素的最大整数值。”。《AscFloor》提供“将src中的浮点数元素按照FLOOR（向负无穷方向舍入）舍入模式截断到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。”，其具体合同或探针直接接入packed floor 与 scalar/Memory/高级接口的同一向负无穷取整语义。
- [Floor](../../../../simd_api/adv_api/math_compute/floor_interface/floor.md)（`same_topic`）：《H2Floor》处理“获取小于或等于输入数据各元素的最大整数值。”。《Floor》提供“获取小于或等于x的最小整数值，即向负无穷取整”，其具体合同或探针直接接入packed floor 与 scalar/Memory/高级接口的同一向负无穷取整语义。
- [Floorf](../../float_math_functions/floorf.md)（`same_topic`）：《Floorf》处理“获取小于或等于输入数据的最大整数值。”。《H2Floor》明确“获取小于或等于输入数据各元素的最大整数值。”，可直接用于核对float floor 与 half/half2、Reg/C API、高阶接口的同一向负无穷取整语义。
- [H2Floor](../../half_type/half2_math_functions/h2floor.md)（`same_topic`）：《H2Floor》处理“获取小于或等于输入数据各元素的最大整数值。”。《H2Floor》提供“获取小于或等于输入数据各元素的最大整数值。”，其具体合同或探针直接接入packed floor 与 scalar/Memory/高级接口的同一向负无穷取整语义。
- [Hfloor](../bfloat16_math_functions/hfloor.md)（`same_topic`）：《H2Floor》处理“获取小于或等于输入数据各元素的最大整数值。”。《Hfloor》提供“获取小于或等于输入bfloat16_t数据的最大整数值。”，其具体合同或探针直接接入packed floor 与 scalar/Memory/高级接口的同一向负无穷取整语义。
- [Hfloor](../../half_type/half_math_functions/hfloor.md)（`same_topic`）：《H2Floor》处理“获取小于或等于输入数据各元素的最大整数值。”。《Hfloor》提供“获取小于或等于输入half数据的最大整数值。”，其具体合同或探针直接接入packed floor 与 scalar/Memory/高级接口的同一向负无穷取整语义。
<!-- cannbot:related:end -->
