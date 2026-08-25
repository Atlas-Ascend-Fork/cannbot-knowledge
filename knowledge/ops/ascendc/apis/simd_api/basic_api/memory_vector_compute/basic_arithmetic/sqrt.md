---
type: API
title: Sqrt
description: 单目矢量计算接口，对输入tensor按元素做开方。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Sqrt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Sqrt

单目矢量计算接口，按元素计算平方根。头文件 `basic_api/kernel_operator_vec_unary_intf.h`。计算公式 dst_i = sqrt(src_i)。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [bisheng 不接受 device 侧 sqrtf—改用向量 Sqrt](../../../../../runbooks/compilation/device_sqrt_uses_vector_api.md)（`exemplifies`）：“bisheng 不接受 device 侧 sqrtf—改用向量 Sqrt”定义：device kernel 中直接调用 sqrtf 导致 bisheng 编译失败；改为 32B 对齐的向量 Sqrt 链并显式同步。；“Sqrt”定义：单目矢量计算接口，对输入tensor按元素做开方。。实质衔接：device sqrtf 编译失败时改用对齐 LocalTensor 的 Vector Sqrt；数值 runbook给出该替换在 Rsqrt 精度修复中的实例，PipeBarrier闭合向量结果消费。
- [dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数](../../../../../runbooks/precision/rsqrt_fast_approximation_use_sqrt_reciprocal.md)（`exemplifies`）：推荐链先用 AscendC::Sqrt，再读取标量做 1.0f/s。
- [AscSqrt](../../../c_api/vector_compute/asc_sqrt.md)（`related`）：C Vector AscSqrt 与 C++ Memory Sqrt 都对 UB tensor 逐元素开方，是跨语言接口的同一计算路径。
- [Rsqrt](rsqrt.md)（`related`）：《Sqrt》明确“单目矢量计算接口，对输入tensor按元素做开方。”；它与《Rsqrt》的“单目矢量计算接口，对输入tensor按元素开方后取倒数。”在实际调用参数、数据流或结果校验上直接衔接。
- [Sqrt](../../reg_vector_compute/basic_arithmetic/sqrt.md)（`related`）：Memory 矢量 Sqrt 与 Reg Sqrt 实现相同逐元素数学操作，但前者以 LocalTensor/count 工作，适用于不同执行路径选型。
- [sqrt（数学函数）](../../../../utils_api/cpp_stdlib/math_functions/sqrt.md)（`related`）：Sqrt说明单目矢量计算接口，对输入tensor按元素做开方。
- [AscSqrt](../../../c_api/reg/arithmetic_compute/asc_sqrt.md)（`same_topic`）：AscSqrt 与《Sqrt》的实质衔接是：Reg C API AscSqrt、Vector C API、Memory API 与 Reg C++ Sqrt 都按元素开方；device sqrtf 构建故障给出改用向量 Sqrt 的可执行修复，Rsqrt 精度卡验证 Sqrt 加倒数的精度路线。
<!-- cannbot:related:end -->
