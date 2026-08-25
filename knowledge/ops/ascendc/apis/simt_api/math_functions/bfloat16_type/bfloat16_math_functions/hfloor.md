---
type: API
title: Hfloor
description: 获取小于或等于输入bfloat16_t数据的最大整数值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_math_functions/hfloor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Hfloor

获取小于或等于输入数据的最大整数值。
函数原型：bfloat16_t hfloor(bfloat16_t x)
返回值：小于或等于输入数据的最大整数值。本接口受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Htrunc](htrunc.md)（`related`）：hfloor 向负无穷取整，而 htrunc 向零截断，负小数输入时结果不同。
- [AscFloor](../../../../simd_api/c_api/reg/data_type_convert/asc_floor.md)（`same_topic`）：《AscFloor》处理“将src中的浮点数元素按照FLOOR（向负无穷方向舍入）舍入模式截断到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。”。《Hfloor》提供“获取小于或等于输入bfloat16_t数据的最大整数值。”，其具体合同或探针直接接入Floor 的 Reg/Memory/高级/SIMT 等价运算语义。
- [Floor](../../../../simd_api/adv_api/math_compute/floor_interface/floor.md)（`same_topic`）：Hfloor 与《Floor》的实质衔接是：Hfloor 对 bfloat16 向负无穷取整；half/packed/float、Hceil/Hrint/Htrunc 和 Tensor/Reg Floor 入口直接对照类型及舍入方向。
- [Floorf](../../float_math_functions/floorf.md)（`same_topic`）：《Floorf》处理“获取小于或等于输入数据的最大整数值。”。《Hfloor》明确“获取小于或等于输入bfloat16_t数据的最大整数值。”，可直接用于核对float floor 与 half/half2、Reg/C API、高阶接口的同一向负无穷取整语义。
- [H2Floor](../bfloat16x2_math_functions/h2floor.md)（`same_topic`）：《H2Floor》处理“获取小于或等于输入数据各元素的最大整数值。”。《Hfloor》提供“获取小于或等于输入bfloat16_t数据的最大整数值。”，其具体合同或探针直接接入packed floor 与 scalar/Memory/高级接口的同一向负无穷取整语义。
- [Hceil](hceil.md)（`same_topic`）：Hfloor 与《Hceil》的实质衔接是：Hfloor 对 bfloat16 向负无穷取整；half/packed/float、Hceil/Hrint/Htrunc 和 Tensor/Reg Floor 入口直接对照类型及舍入方向。
- [Hfloor](../../half_type/half_math_functions/hfloor.md)（`same_topic`）：《Hfloor》处理“获取小于或等于输入half数据的最大整数值。”。《Hfloor》明确“获取小于或等于输入bfloat16_t数据的最大整数值。”，可直接用于核对half floor 与 float/half2、Reg/C API、高阶接口的同一取整语义。
- [Hrint](hrint.md)（`same_topic`）：Hfloor 与《Hrint》的实质衔接是：Hfloor 对 bfloat16 向负无穷取整；half/packed/float、Hceil/Hrint/Htrunc 和 Tensor/Reg Floor 入口直接对照类型及舍入方向。
<!-- cannbot:related:end -->
