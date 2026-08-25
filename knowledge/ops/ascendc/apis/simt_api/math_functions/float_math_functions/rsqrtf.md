---
type: API
title: Rsqrtf
description: 获取输入数据x的平方根的倒数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/rsqrtf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Rsqrtf

功能：获取输入数据x的平方根的倒数。

函数原型：float rsqrtf(float x)

参数：x（输入）源操作数，输入数据。

返回值：输入数据的平方根的倒数。特殊值：0→inf；inf→0；-inf→nan；nan→nan。

约束：本接口支持的输入数据范围为x大于等于0，否则返回值为nan。 针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：本接口内部实现使用到了sqrtf，由于sqrtf不支持Subnormal场景，当输入x为Subnormal数据时，会导致本接口最终结果为+inf。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数](../../../../runbooks/precision/rsqrt_fast_approximation_use_sqrt_reciprocal.md)（`exemplifies`）：该 runbook 以实测约 2^-9 误差说明快速 Rsqrt 的精度边界，并验证 Sqrt 后标量倒数可恢复 fp32 精度。
- [Hrsqrt](../bfloat16_type/bfloat16_math_functions/hrsqrt.md)（`related`）：《Hrsqrt》说明计算bfloat16_t输入数据x的平方根的倒数。；《Rsqrtf》说明获取输入数据x的平方根的倒数。。二者在Hrsqrt等价于平方根后取倒数，跨half/bfloat16x2/float/Vector实现及精度故障可直接验证结果与误差边界上存在可执行的直接衔接。
- [Sqrtf](sqrtf.md)（`related`）：Rsqrtf 返回 1/sqrt(x)，Sqrtf 返回 sqrt(x)，二者是同一输入域的正向与倒数路径。
- [AscRsqrt](../../../simd_api/c_api/vector_compute/asc_rsqrt.md)（`same_topic`）：焦点处理逐元素 Rsqrt 的类型变体与精度回退；Rsqrtf正文界定“获取输入数据x的平方根的倒数”。候选保持 sqrt-reciprocal 数学语义，覆盖 dtype 变体、AscRcp 组合及已验证精度回退。
<!-- cannbot:related:end -->
