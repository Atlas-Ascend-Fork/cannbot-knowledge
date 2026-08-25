---
type: API
title: Htrunc
description: 获取对输入bfloat16_t数据浮点数截断后的整数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_math_functions/htrunc.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Htrunc

获取对输入数据的浮点数截断后的整数。
函数原型：bfloat16_t htrunc(bfloat16_t x)
返回值：输入数据浮点数截断后的整数。本接口受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscTrunc](../../../../simd_api/c_api/reg/data_type_convert/asc_trunc.md)（`related`）：《AscTrunc》说明将浮点数按TRUNC（向零方向截断）截断为整数值，结果保持原浮点类型。；《Htrunc》说明获取对输入bfloat16_t数据浮点数截断后的整数。。二者在AscTrunc与Memory Trunc、SIMT half/bfloat16/float变体共享向零截断语义，workspace查询用于高阶接口分块上存在可执行的直接衔接。
- [Hfloor](hfloor.md)（`related`）：hfloor 向负无穷取整，而 htrunc 向零截断，负小数输入时结果不同。
- [Hrint](hrint.md)（`related`）：hrint 取最近偶数，与 htrunc 的向零语义构成另一舍入选择。
- [Htrunc](../../half_type/half_math_functions/htrunc.md)（`related`）：两接口都把标量 16 位浮点截断到整数值，分别面向 half 和 bfloat16。
- [Truncate](../../../../simd_api/basic_api/memory_vector_compute/type_conversion/truncate_isasi.md)（`same_topic`）：《Truncate》处理“将源操作数的浮点数元素截断到整数位，保持原数据类型不变，支持多种舍入模式。”。《Htrunc》明确“获取对输入bfloat16_t数据浮点数截断后的整数。”，可直接用于核对Truncate 向零取整在 Cast round-mode、高阶/基础/SIMT 接口中的等价语义。
- [Truncf](../../float_math_functions/truncf.md)（`same_topic`）：Truncf 与《Htrunc》的实质衔接是：Truncf 与 SIMD、基础、C、half/half2/bfloat16x2 Trunc 都实现向零截断；空间查询只适用于高阶 tensor 版本，不能套到标量入口。
<!-- cannbot:related:end -->
