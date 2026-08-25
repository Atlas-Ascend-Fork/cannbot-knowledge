---
type: API
title: Sqrtf
description: 获取输入数据x的平方根。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/sqrtf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Sqrtf

功能：获取输入数据x的平方根。

函数原型：float sqrtf(float x)

参数：x（输入）源操作数，输入数据。

返回值：输入数据的平方根。特殊值：0→0；inf→inf；-inf→nan；nan→nan。

约束：本接口支持的输入数据范围为x大于等于0，否则返回值为nan。 针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：处于Subnormal范围内的输入和输出值，都会被刷新为保留符号的0。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [bisheng 不接受 device 侧 sqrtf—改用向量 Sqrt](../../../../runbooks/compilation/device_sqrt_uses_vector_api.md)（`exemplifies`）：Runbook 记录在 __aicore__ 普通 device 路径直接调用 libc sqrtf 的 bisheng 失败，并以 32B LocalTensor 上 AscendC::Sqrt、显式同步和全量精度通过收敛，为 SIMT sqrtf 卡补充编程域边界。
- [Rsqrtf](rsqrtf.md)（`related`）：Rsqrtf 返回 1/sqrt(x)，Sqrtf 返回 sqrt(x)，二者是同一输入域的正向与倒数路径。
- [Hsqrt](../bfloat16_type/bfloat16_math_functions/hsqrt.md)（`same_topic`）：Hsqrt 与《Sqrtf》的实质衔接是：bfloat16 Hsqrt 与同类型 Hrsqrt 分别执行 sqrt 和 reciprocal-sqrt；bfloat16x2、half 与 float 的 sqrt 入口保持数学任务一致，但返回宽度、次正规数和特殊值契约不同。
<!-- cannbot:related:end -->
