---
type: API
title: Rsqrt
description: 单目矢量计算接口，对输入tensor按元素开方后取倒数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Rsqrt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Rsqrt

单目矢量计算接口，按元素计算平方根倒数。头文件 `basic_api/kernel_operator_vec_unary_intf.h`。计算公式 dst_i = 1/sqrt(src_i)。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数](../../../../../runbooks/precision/rsqrt_fast_approximation_use_sqrt_reciprocal.md)（`exemplifies`）：低精度信号来自不带 config 的 AscendC::Rsqrt<float>；接口用于核对实际重载和精度配置。
- [Hrsqrt](../../../../simt_api/math_functions/bfloat16_type/bfloat16_math_functions/hrsqrt.md)（`related`）：《Hrsqrt》说明计算bfloat16_t输入数据x的平方根的倒数。；《Rsqrt》说明单目矢量计算接口，对输入tensor按元素开方后取倒数。。二者在Hrsqrt等价于平方根后取倒数，跨half/bfloat16x2/float/Vector实现及精度故障可直接验证结果与误差边界上存在可执行的直接衔接。
- [Sqrt](sqrt.md)（`related`）：《Sqrt》明确“单目矢量计算接口，对输入tensor按元素做开方。”；它与《Rsqrt》的“单目矢量计算接口，对输入tensor按元素开方后取倒数。”在实际调用参数、数据流或结果校验上直接衔接。
- [AscRsqrt](../../../c_api/vector_compute/asc_rsqrt.md)（`same_topic`）：焦点处理逐元素 Rsqrt 的类型变体与精度回退；Rsqrt正文界定“单目矢量计算接口，对输入tensor按元素开方后取倒数”。候选保持 sqrt-reciprocal 数学语义，覆盖 dtype 变体、AscRcp 组合及已验证精度回退。
- [H2Rsqrt](../../../../simt_api/math_functions/half_type/half2_math_functions/h2rsqrt.md)（`same_topic`）：Tensor Rsqrt 在 LocalTensor 上提供同一倒平方根语义，可按 SIMT packed 或 SIMD tensor 数据路径选型。
<!-- cannbot:related:end -->
