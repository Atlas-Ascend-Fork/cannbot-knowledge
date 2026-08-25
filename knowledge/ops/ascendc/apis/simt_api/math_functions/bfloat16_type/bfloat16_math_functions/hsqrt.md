---
type: API
title: Hsqrt
description: 计算bfloat16_t输入数据x的平方根。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_math_functions/hsqrt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Hsqrt

获取输入数据x的平方根。
函数原型：bfloat16_t hsqrt(bfloat16_t x)
返回值：输入数据的平方根。本接口受全局饱和模式影响，特殊值如下：
约束：本接口支持的输入数据范围为x大于等于0，否则返回值为nan。；针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：处于Subnormal范围内的输入和输出值，都会被刷新为保留符号的0。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Hrsqrt](hrsqrt.md)（`related`）：《Hrsqrt》说明计算bfloat16_t输入数据x的平方根的倒数。；《Hsqrt》说明计算bfloat16_t输入数据x的平方根。。二者在Hrsqrt等价于平方根后取倒数，跨half/bfloat16x2/float/Vector实现及精度故障可直接验证结果与误差边界上存在可执行的直接衔接。
- [Hsqrt](../../half_type/half_math_functions/hsqrt.md)（`related`）：bfloat16 Hsqrt 提供相同平方根语义的另一 16 位格式，可用于核对 half 与 bfloat16 的饱和/特殊值差异。
- [H2Sqrt](../bfloat16x2_math_functions/h2sqrt.md)（`same_topic`）：Hsqrt 与《H2Sqrt》的实质衔接是：bfloat16 Hsqrt 与同类型 Hrsqrt 分别执行 sqrt 和 reciprocal-sqrt；bfloat16x2、half 与 float 的 sqrt 入口保持数学任务一致，但返回宽度、次正规数和特殊值契约不同。
- [Sqrtf](../../float_math_functions/sqrtf.md)（`same_topic`）：Hsqrt 与《Sqrtf》的实质衔接是：bfloat16 Hsqrt 与同类型 Hrsqrt 分别执行 sqrt 和 reciprocal-sqrt；bfloat16x2、half 与 float 的 sqrt 入口保持数学任务一致，但返回宽度、次正规数和特殊值契约不同。
- [bfloat16类型数学库函数](bfloat16_math_functions.md)（`same_topic`）：Hsqrt 与《bfloat16类型数学库函数》的实质衔接是：bfloat16 Hsqrt 与同类型 Hrsqrt 分别执行 sqrt 和 reciprocal-sqrt；bfloat16x2、half 与 float 的 sqrt 入口保持数学任务一致，但返回宽度、次正规数和特殊值契约不同。
<!-- cannbot:related:end -->
