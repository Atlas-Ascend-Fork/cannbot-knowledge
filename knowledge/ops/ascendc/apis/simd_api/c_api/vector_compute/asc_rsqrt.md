---
type: API
title: AscRsqrt
description: 按元素进行开方后取倒数的计算，
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_rsqrt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscRsqrt

按元素进行开方后取倒数的计算，计算公式如下：
函数原型：void asc_rsqrt(__ubuf__ half* dst, __ubuf__ half* src, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数](../../../../runbooks/precision/rsqrt_fast_approximation_use_sqrt_reciprocal.md)（`exemplifies`）：焦点处理逐元素 Rsqrt 的类型变体与精度回退；dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数正文界定“RmsNorm 的 fp32 rstd 使用不带 config 的 Rsqrt 后呈现约 2^-9 量化偏差；改为 Sqrt、标量读回与 1.0f/s 后恢复 fp32 精度”。候选保持 sqrt-reciprocal 数学语义，覆盖 dtype 变体、AscRcp 组合及已验证精度回退。
- [AscRcp](asc_rcp.md)（`related`）：焦点处理逐元素 Rsqrt 的类型变体与精度回退；AscRcp正文界定“执行矢量的取倒数运算”。候选保持 sqrt-reciprocal 数学语义，覆盖 dtype 变体、AscRcp 组合及已验证精度回退。
- [AscSqrt](../reg/arithmetic_compute/asc_sqrt.md)（`related`）：焦点处理逐元素 Rsqrt 的类型变体与精度回退；AscSqrt正文界定“根据mask对源操作数src按元素求开方，将结果写入目的操作数dst”。候选保持 sqrt-reciprocal 数学语义，覆盖 dtype 变体、AscRcp 组合及已验证精度回退。
- [Hrsqrt](../../../simt_api/math_functions/bfloat16_type/bfloat16_math_functions/hrsqrt.md)（`related`）：《Hrsqrt》说明计算bfloat16_t输入数据x的平方根的倒数。；《AscRsqrt》说明按元素进行开方后取倒数的计算，。二者在Hrsqrt等价于平方根后取倒数，跨half/bfloat16x2/float/Vector实现及精度故障可直接验证结果与误差边界上存在可执行的直接衔接。
- [H2Rsqrt](../../../simt_api/math_functions/bfloat16_type/bfloat16x2_math_functions/h2rsqrt.md)（`same_topic`）：焦点处理逐元素 Rsqrt 的类型变体与精度回退；H2Rsqrt正文界定“获取输入数据x各元素的平方根的倒数”。候选保持 sqrt-reciprocal 数学语义，覆盖 dtype 变体、AscRcp 组合及已验证精度回退。
- [H2Rsqrt](../../../simt_api/math_functions/half_type/half2_math_functions/h2rsqrt.md)（`same_topic`）：焦点处理逐元素 Rsqrt 的类型变体与精度回退；H2Rsqrt正文界定“获取输入数据x各元素的平方根的倒数”。候选保持 sqrt-reciprocal 数学语义，覆盖 dtype 变体、AscRcp 组合及已验证精度回退。
- [Hrsqrt](../../../simt_api/math_functions/half_type/half_math_functions/hrsqrt.md)（`same_topic`）：焦点处理逐元素 Rsqrt 的类型变体与精度回退；Hrsqrt正文界定“计算half输入数据x的平方根的倒数”。候选保持 sqrt-reciprocal 数学语义，覆盖 dtype 变体、AscRcp 组合及已验证精度回退。
- [Rsqrt](../../basic_api/memory_vector_compute/basic_arithmetic/rsqrt.md)（`same_topic`）：焦点处理逐元素 Rsqrt 的类型变体与精度回退；Rsqrt正文界定“单目矢量计算接口，对输入tensor按元素开方后取倒数”。候选保持 sqrt-reciprocal 数学语义，覆盖 dtype 变体、AscRcp 组合及已验证精度回退。
- [Rsqrtf](../../../simt_api/math_functions/float_math_functions/rsqrtf.md)（`same_topic`）：焦点处理逐元素 Rsqrt 的类型变体与精度回退；Rsqrtf正文界定“获取输入数据x的平方根的倒数”。候选保持 sqrt-reciprocal 数学语义，覆盖 dtype 变体、AscRcp 组合及已验证精度回退。
<!-- cannbot:related:end -->
