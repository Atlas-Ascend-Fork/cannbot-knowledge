---
type: API
title: AscSqrt
description: 根据mask对源操作数src按元素求开方，将结果写入目的操作数dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_sqrt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscSqrt

该接口根据mask，对源操作数src进行按元素求开方操作，将结果写入目的操作数dst。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器）。用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：float、half。

约束：- mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。
- 输入为负数时结果为nan。
- 输入为-0时结果为-0。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [bisheng 不接受 device 侧 sqrtf—改用向量 Sqrt](../../../../../runbooks/compilation/device_sqrt_uses_vector_api.md)（`exemplifies`）：AscSqrt 与《bisheng 不接受 device 侧 sqrtf—改用向量 Sqrt》的实质衔接是：Reg C API AscSqrt、Vector C API、Memory API 与 Reg C++ Sqrt 都按元素开方；device sqrtf 构建故障给出改用向量 Sqrt 的可执行修复，Rsqrt 精度卡验证 Sqrt 加倒数的精度路线。
- [dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数](../../../../../runbooks/precision/rsqrt_fast_approximation_use_sqrt_reciprocal.md)（`exemplifies`）：AscSqrt 与《dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数》的实质衔接是：Reg C API AscSqrt、Vector C API、Memory API 与 Reg C++ Sqrt 都按元素开方；device sqrtf 构建故障给出改用向量 Sqrt 的可执行修复，Rsqrt 精度卡验证 Sqrt 加倒数的精度路线。
- [AscRsqrt](../../vector_compute/asc_rsqrt.md)（`related`）：焦点处理逐元素 Rsqrt 的类型变体与精度回退；AscSqrt正文界定“根据mask对源操作数src按元素求开方，将结果写入目的操作数dst”。候选保持 sqrt-reciprocal 数学语义，覆盖 dtype 变体、AscRcp 组合及已验证精度回退。
- [sqrt（数学函数）](../../../../utils_api/cpp_stdlib/math_functions/sqrt.md)（`related`）：AscSqrt说明根据mask对源操作数src按元素求开方，将结果写入目的操作数dst。
- [AscSqrt](../../vector_compute/asc_sqrt.md)（`same_topic`）：AscSqrt 与《AscSqrt》的实质衔接是：Reg C API AscSqrt、Vector C API、Memory API 与 Reg C++ Sqrt 都按元素开方；device sqrtf 构建故障给出改用向量 Sqrt 的可执行修复，Rsqrt 精度卡验证 Sqrt 加倒数的精度路线。
- [Sqrt](../../../basic_api/memory_vector_compute/basic_arithmetic/sqrt.md)（`same_topic`）：AscSqrt 与《Sqrt》的实质衔接是：Reg C API AscSqrt、Vector C API、Memory API 与 Reg C++ Sqrt 都按元素开方；device sqrtf 构建故障给出改用向量 Sqrt 的可执行修复，Rsqrt 精度卡验证 Sqrt 加倒数的精度路线。
- [Sqrt](../../../basic_api/reg_vector_compute/basic_arithmetic/sqrt.md)（`same_topic`）：AscSqrt 与《Sqrt》的实质衔接是：Reg C API AscSqrt、Vector C API、Memory API 与 Reg C++ Sqrt 都按元素开方；device sqrtf 构建故障给出改用向量 Sqrt 的可执行修复，Rsqrt 精度卡验证 Sqrt 加倒数的精度路线。
<!-- cannbot:related:end -->
