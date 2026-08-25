---
type: API
title: Hrsqrt
description: 计算bfloat16_t输入数据x的平方根的倒数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_math_functions/hrsqrt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Hrsqrt

获取输入数据x的平方根的倒数。
函数原型：bfloat16_t hrsqrt(bfloat16_t x)
返回值：输入数据的平方根的倒数。本接口受全局饱和模式影响，特殊值如下：
约束：本接口支持的输入数据范围为x大于等于0，否则返回值为nan。；针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：本接口内部实现使用到了sqrtf，由于sqrtf不支持Subnormal场景，当输入x为Subnormal数据时，会导致本接口最终结果为+inf。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数](../../../../../runbooks/precision/rsqrt_fast_approximation_use_sqrt_reciprocal.md)（`exemplifies`）：《Hrsqrt》说明计算bfloat16_t输入数据x的平方根的倒数。；《dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数》说明RmsNorm 的 fp32 rstd 使用不带 config 的 Rsqrt 后呈现约 2^-9 量化偏差；改为 Sqrt、标量读回与 1.0f/s 后恢复 fp32 精度。。二者在Hrsqrt等价于平方根后取倒数，跨half/bfloat16x2/float/Vector实现及精度故障可直接验证结果与误差边界上存在可执行的直接衔接。
- [AscRsqrt](../../../../simd_api/c_api/vector_compute/asc_rsqrt.md)（`related`）：《Hrsqrt》说明计算bfloat16_t输入数据x的平方根的倒数。；《AscRsqrt》说明按元素进行开方后取倒数的计算，。二者在Hrsqrt等价于平方根后取倒数，跨half/bfloat16x2/float/Vector实现及精度故障可直接验证结果与误差边界上存在可执行的直接衔接。
- [Hsqrt](hsqrt.md)（`related`）：《Hrsqrt》说明计算bfloat16_t输入数据x的平方根的倒数。；《Hsqrt》说明计算bfloat16_t输入数据x的平方根。。二者在Hrsqrt等价于平方根后取倒数，跨half/bfloat16x2/float/Vector实现及精度故障可直接验证结果与误差边界上存在可执行的直接衔接。
- [Rsqrt](../../../../simd_api/basic_api/memory_vector_compute/basic_arithmetic/rsqrt.md)（`related`）：《Hrsqrt》说明计算bfloat16_t输入数据x的平方根的倒数。；《Rsqrt》说明单目矢量计算接口，对输入tensor按元素开方后取倒数。。二者在Hrsqrt等价于平方根后取倒数，跨half/bfloat16x2/float/Vector实现及精度故障可直接验证结果与误差边界上存在可执行的直接衔接。
- [Rsqrtf](../../float_math_functions/rsqrtf.md)（`related`）：《Hrsqrt》说明计算bfloat16_t输入数据x的平方根的倒数。；《Rsqrtf》说明获取输入数据x的平方根的倒数。。二者在Hrsqrt等价于平方根后取倒数，跨half/bfloat16x2/float/Vector实现及精度故障可直接验证结果与误差边界上存在可执行的直接衔接。
- [H2Rsqrt](../bfloat16x2_math_functions/h2rsqrt.md)（`same_topic`）：《Hrsqrt》说明计算bfloat16_t输入数据x的平方根的倒数。；《H2Rsqrt》说明获取输入数据x各元素的平方根的倒数。。二者在Hrsqrt等价于平方根后取倒数，跨half/bfloat16x2/float/Vector实现及精度故障可直接验证结果与误差边界上存在可执行的直接衔接。
- [H2Rsqrt](../../half_type/half2_math_functions/h2rsqrt.md)（`same_topic`）：《Hrsqrt》说明计算bfloat16_t输入数据x的平方根的倒数。；《H2Rsqrt》说明获取输入数据x各元素的平方根的倒数。。二者在Hrsqrt等价于平方根后取倒数，跨half/bfloat16x2/float/Vector实现及精度故障可直接验证结果与误差边界上存在可执行的直接衔接。
- [Hrsqrt](../../half_type/half_math_functions/hrsqrt.md)（`same_topic`）：《Hrsqrt》说明计算bfloat16_t输入数据x的平方根的倒数。；《Hrsqrt》说明计算half输入数据x的平方根的倒数。。二者在Hrsqrt等价于平方根后取倒数，跨half/bfloat16x2/float/Vector实现及精度故障可直接验证结果与误差边界上存在可执行的直接衔接。
<!-- cannbot:related:end -->
