---
type: API
title: Ln
description: 单目矢量计算接口，对输入tensor按元素取自然对数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Ln.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Ln

单目矢量计算接口，按元素计算自然对数。头文件 `basic_api/kernel_operator_vec_unary_intf.h`。计算公式 dst_i = ln(src_i)。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [Exp](exp.md)（`related`）：Ln 是 Exp 的反函数，可在有限正常数范围构造往返精度测试。
<!-- cannbot:related:end -->
