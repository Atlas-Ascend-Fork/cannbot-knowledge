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

- [dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数](../../../../../runbooks/precision/rsqrt_fast_approximation_use_sqrt_reciprocal.md)（`exemplifies`）：本轨迹中不带 config 的 `Rsqrt<float>` 在 dav-2201 上产生约 9-bit 量级的快速倒数结果。；单目矢量计算接口，按元素计算平方根倒数。头文件 `basic_api/kernel_operator_vec_unary_intf.h`。计算公式 dst_i = 1/sqrt(src_i)。API 卡定义被调用的运算，runbook 给出 dav-2201 上该调用形态的精度失败信号与 Sqrt+标量倒数替代方案。
<!-- cannbot:related:end -->
