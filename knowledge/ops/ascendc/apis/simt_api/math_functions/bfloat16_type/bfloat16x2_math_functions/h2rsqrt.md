---
type: API
title: H2Rsqrt
description: 获取输入数据x各元素的平方根的倒数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_math_functions/h2rsqrt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# H2Rsqrt

功能：获取输入数据x各元素的平方根的倒数。

函数原型：bfloat16x2_t h2rsqrt(bfloat16x2_t x)

参数：x（输入）源操作数，输入数据。

返回值：输入数据各元素的平方根的倒数。本接口受全局饱和模式影响，。特殊值：0→ASCRT_MAX_NORMAL_BF16；-0→ASCRT_MAX_NORMAL_BF16；nan→0；inf→0；-inf→0。

约束：本接口支持的输入数据范围为x大于等于0，否则返回值为nan。 针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：本接口内部实现使用到了sqrtf，由于sqrtf不支持Subnormal场景，当输入x为Subnormal数据时，会导致本接口最终结果为+inf。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数](../../../../../runbooks/precision/rsqrt_fast_approximation_use_sqrt_reciprocal.md)（`exemplifies`）：H2Rsqrt 与《dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数》的实质衔接是：H2Rsqrt 与 sqrt/rcp、half/float Rsqrt 及精度替代卡共同界定倒数平方根实现。
- [H2Sqrt](h2sqrt.md)（`related`）：H2Sqrt 返回平方根，H2Rsqrt 返回平方根倒数；归一化公式需要倒数时可避免再除法。
- [AscRsqrt](../../../../simd_api/c_api/vector_compute/asc_rsqrt.md)（`same_topic`）：焦点处理逐元素 Rsqrt 的类型变体与精度回退；H2Rsqrt正文界定“获取输入数据x各元素的平方根的倒数”。候选保持 sqrt-reciprocal 数学语义，覆盖 dtype 变体、AscRcp 组合及已验证精度回退。
- [H2Rcp](h2rcp.md)（`same_topic`）：H2Rsqrt 与《H2Rcp》的实质衔接是：H2Rsqrt 与 sqrt/rcp、half/float Rsqrt 及精度替代卡共同界定倒数平方根实现。
- [H2Rsqrt](../../half_type/half2_math_functions/h2rsqrt.md)（`same_topic`）：bfloat16x2 与 half2 版本都做两 lane 倒平方根，输入精度不同，适合按 packed dtype 映射。
- [Hrsqrt](../bfloat16_math_functions/hrsqrt.md)（`same_topic`）：《Hrsqrt》说明计算bfloat16_t输入数据x的平方根的倒数。；《H2Rsqrt》说明获取输入数据x各元素的平方根的倒数。。二者在Hrsqrt等价于平方根后取倒数，跨half/bfloat16x2/float/Vector实现及精度故障可直接验证结果与误差边界上存在可执行的直接衔接。
<!-- cannbot:related:end -->
