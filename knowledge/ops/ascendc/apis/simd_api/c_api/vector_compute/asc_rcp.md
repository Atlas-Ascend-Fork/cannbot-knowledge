---
type: API
title: AscRcp
description: 执行矢量的取倒数运算。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_rcp.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscRcp

执行矢量的取倒数运算。计算公式如下：
函数原型：void asc_rcp(__ubuf__ half* dst, __ubuf__ half* src, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscRsqrt](asc_rsqrt.md)（`related`）：焦点处理逐元素 Rsqrt 的类型变体与精度回退；AscRcp正文界定“执行矢量的取倒数运算”。候选保持 sqrt-reciprocal 数学语义，覆盖 dtype 变体、AscRcp 组合及已验证精度回退。
- [Reciprocal](../../basic_api/memory_vector_compute/basic_arithmetic/reciprocal.md)（`related`）：AscRcp 与《Reciprocal》都执行逐元素倒数；前者是 A2/A3 的 C 指针接口，后者是 LocalTensor 基础 API，操作契约相同而调用层不同。
<!-- cannbot:related:end -->
