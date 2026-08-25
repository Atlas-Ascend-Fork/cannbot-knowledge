---
type: API
title: AscSqrt
description: asc_sqrt（矢量计算）
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_sqrt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscSqrt

按元素做开方，计算公式如下：
函数原型：void asc_sqrt(__ubuf__ half* dst, __ubuf__ half* src, uint32_t count)
参数：dst（输出）：目的操作数（矢量）的起始地址。；src（输入）：源操作数（矢量）的起始地址。；count（输入）：参与计算的元素个数。
约束：src只支持设置为正数。；操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [bisheng 不接受 device 侧 sqrtf—改用向量 Sqrt](../../../../runbooks/compilation/device_sqrt_uses_vector_api.md)（`exemplifies`）：该 runbook 记录 device 标量 sqrtf 不可编译时改用 32B 对齐 Vector Sqrt 并显式同步，给出 AscSqrt 路线的实际选择依据。
- [Sqrt](../../basic_api/memory_vector_compute/basic_arithmetic/sqrt.md)（`related`）：C Vector AscSqrt 与 C++ Memory Sqrt 都对 UB tensor 逐元素开方，是跨语言接口的同一计算路径。
- [sqrt（数学函数）](../../../utils_api/cpp_stdlib/math_functions/sqrt.md)（`related`）：AscSqrt说明asc_sqrt（矢量计算）。
- [AscSqrt](../reg/arithmetic_compute/asc_sqrt.md)（`same_topic`）：AscSqrt 与《AscSqrt》的实质衔接是：Reg C API AscSqrt、Vector C API、Memory API 与 Reg C++ Sqrt 都按元素开方；device sqrtf 构建故障给出改用向量 Sqrt 的可执行修复，Rsqrt 精度卡验证 Sqrt 加倒数的精度路线。
<!-- cannbot:related:end -->
