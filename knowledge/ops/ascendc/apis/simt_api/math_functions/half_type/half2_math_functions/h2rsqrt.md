---
type: API
title: H2Rsqrt
description: 获取输入数据x各元素的平方根的倒数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_math_functions/h2rsqrt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# H2Rsqrt

功能：获取输入数据x各元素的平方根的倒数。

函数原型：half2 h2rsqrt(half2 x)

参数：x（输入）源操作数，输入数据。

返回值：输入数据各元素的平方根的倒数。本接口受全局饱和寄存器影响，。特殊值：0→ASCRT_MAX_NORMAL_FP16；-0→-ASCRT_MAX_NORMAL_FP16；nan→ASCRT_MAX_NORMAL_FP16；-inf→ASCRT_MAX_NORMAL_FP16；inf→1.52588e-05。

约束：本接口支持的输入数据范围为x大于等于0，否则返回值为nan。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Rcp](h2rcp.md)（`related`）：h2rsqrt 可视为 sqrt 与 reciprocal 的融合目标，h2rcp 用于拆分实现或精度对照。
- [H2Sqrt](h2sqrt.md)（`related`）：H2Sqrt 返回平方根，H2Rsqrt 返回平方根倒数；同一 half2 输入在归一化等场景可选择直接 rsqrt 或 sqrt 后求倒数，特殊值结果不同。
- [AscRsqrt](../../../../simd_api/c_api/vector_compute/asc_rsqrt.md)（`same_topic`）：焦点处理逐元素 Rsqrt 的类型变体与精度回退；H2Rsqrt正文界定“获取输入数据x各元素的平方根的倒数”。候选保持 sqrt-reciprocal 数学语义，覆盖 dtype 变体、AscRcp 组合及已验证精度回退。
- [H2Rsqrt](../../bfloat16_type/bfloat16x2_math_functions/h2rsqrt.md)（`same_topic`）：bfloat16x2 与 half2 版本都做两 lane 倒平方根，输入精度不同，适合按 packed dtype 映射。
- [Hrsqrt](../../bfloat16_type/bfloat16_math_functions/hrsqrt.md)（`same_topic`）：《Hrsqrt》说明计算bfloat16_t输入数据x的平方根的倒数。；《H2Rsqrt》说明获取输入数据x各元素的平方根的倒数。。二者在Hrsqrt等价于平方根后取倒数，跨half/bfloat16x2/float/Vector实现及精度故障可直接验证结果与误差边界上存在可执行的直接衔接。
- [Rsqrt](../../../../simd_api/basic_api/memory_vector_compute/basic_arithmetic/rsqrt.md)（`same_topic`）：Tensor Rsqrt 在 LocalTensor 上提供同一倒平方根语义，可按 SIMT packed 或 SIMD tensor 数据路径选型。
<!-- cannbot:related:end -->
