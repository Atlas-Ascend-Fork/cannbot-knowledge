---
type: API
title: Hrsqrt
description: 计算half输入数据x的平方根的倒数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_math_functions/hrsqrt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Hrsqrt

功能：获取输入数据x的平方根的倒数。

函数原型：half hrsqrt(half x)

参数：x（输入）源操作数，输入数据。

返回值：输入数据的平方根的倒数。本接口受全局饱和寄存器的影响，。特殊值：0→ASCRT_MAX_NORMAL_FP16；-0→-ASCRT_MAX_NORMAL_FP16；nan→ASCRT_MAX_NORMAL_FP16；inf→0；-inf→ASCRT_MAX_NORMAL_FP16。

约束：本接口支持的输入数据范围为x大于等于0，否则返回值为nan。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数](../../../../../runbooks/precision/rsqrt_fast_approximation_use_sqrt_reciprocal.md)（`exemplifies`）：Hrsqrt 与《dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数》的实质衔接是：Hrsqrt 可由 Hsqrt 与 Hrcp 分解；精度故障卡给出该替换在实测误差超限时的可执行验证。
- [Hsqrt](hsqrt.md)（`related`）：Hrsqrt 计算 1/sqrt(x)，与 Hsqrt 共享非负输入域但输出语义增加倒数；两者常用于在精度与后续除法链之间选型。
- [AscRsqrt](../../../../simd_api/c_api/vector_compute/asc_rsqrt.md)（`same_topic`）：焦点处理逐元素 Rsqrt 的类型变体与精度回退；Hrsqrt正文界定“计算half输入数据x的平方根的倒数”。候选保持 sqrt-reciprocal 数学语义，覆盖 dtype 变体、AscRcp 组合及已验证精度回退。
- [Half数学函数hrcp](hrcp.md)（`same_topic`）：Hrsqrt 与《Half数学函数hrcp》的实质衔接是：Hrsqrt 可由 Hsqrt 与 Hrcp 分解；精度故障卡给出该替换在实测误差超限时的可执行验证。
- [Hrsqrt](../../bfloat16_type/bfloat16_math_functions/hrsqrt.md)（`same_topic`）：《Hrsqrt》说明计算bfloat16_t输入数据x的平方根的倒数。；《Hrsqrt》说明计算half输入数据x的平方根的倒数。。二者在Hrsqrt等价于平方根后取倒数，跨half/bfloat16x2/float/Vector实现及精度故障可直接验证结果与误差边界上存在可执行的直接衔接。
<!-- cannbot:related:end -->
