---
type: API
title: Reciprocal
description: 单目矢量计算接口，对输入tensor按元素取倒数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Reciprocal.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Reciprocal

单目矢量计算接口，按元素计算倒数。头文件 `basic_api/kernel_operator_vec_unary_intf.h`。计算公式 dst_i = 1/src_i。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [Reciprocal 低精度致 sigmoid 比对失败](../../../../../runbooks/precision/reciprocal_sigmoid.md)（`exemplifies`）：焦点卡把误差单点归因到“`AscendC::Reciprocal(yLocal, tmp, count)`”，候选卡规定该接口“计算公式 dst_i = 1/src_i”；接口正是 sigmoid 最后一步倒数的实现点，runbook补充 A2 严格精度下应改 Duplicate+Div 的验证边界。
<!-- cannbot:related:end -->
