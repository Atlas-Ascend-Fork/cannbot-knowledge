---
type: API
title: SetKernelMode
description: CPU调测时设置内核模式为AIV、AIC或MIX模式，分别支持矢量、矩阵和混合算子调试。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/cpu_twin_debug/SetKernelMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetKernelMode

CPU 调测时设置内核模式：AIV（矢量算子）、AIC（矩阵算子）或 MIX（混合模式）。参数 mode 为 KernelMode 枚举。仅 CPU 调测使用。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [直调 kernel-type 裸赋值标记无效](../../../../../runbooks/compilation/kernel_type.md)（`exemplifies`）：SetKernelMode 与《直调 kernel-type 裸赋值标记无效》的实质衔接是：SetKernelMode 仅在 CPU 调测选择 AIV/AIC/MIX；孪生调试指南、kernel 类型设置和两个错误配置案例限定调测与生产启动的边界。
- [空 Ascend C kernel 骨架需显式标注 Vector 执行类型](../../../../../runbooks/compilation/empty_kernel_requires_explicit_vector_type.md)（`exemplifies`）：SetKernelMode 与《空 Ascend C kernel 骨架需显式标注 Vector 执行类型》的实质衔接是：SetKernelMode 仅在 CPU 调测选择 AIV/AIC/MIX；孪生调试指南、kernel 类型设置和两个错误配置案例限定调测与生产启动的边界。
- [CPU域孪生调试（功能调试）](../../../../../guides/programming_guide/debug_and_tuning/functional_debug/cpu_twin_debug.md)（`explains`）：SetKernelMode 与《CPU域孪生调试（功能调试）》的实质衔接是：SetKernelMode 仅在 CPU 调测选择 AIV/AIC/MIX；孪生调试指南、kernel 类型设置和两个错误配置案例限定调测与生产启动的边界。
- [设置合适的核数和算子Kernel类型](../../../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/core_count_kernel_type.md)（`explains`）：设置合适的核数和算子Kernel类型 与《SetKernelMode》的实质衔接是：核数、kernel 类型和 workspace 都会影响启动/头尾开销；SetKernelMode、负载均衡与 SK_BIND 卡给出 host 配置和核侧绑定的执行落点。
- [CPU孪生调试](cpu_twin_debug.md)（`same_topic`）：SetKernelMode 与《CPU孪生调试》的实质衔接是：SetKernelMode 仅在 CPU 调测选择 AIV/AIC/MIX；孪生调试指南、kernel 类型设置和两个错误配置案例限定调测与生产启动的边界。
- [设置Kernel类型](../../kernel_tiling/set_kernel_type.md)（`same_topic`）：SetKernelMode 与《设置Kernel类型》的实质衔接是：SetKernelMode 仅在 CPU 调测选择 AIV/AIC/MIX；孪生调试指南、kernel 类型设置和两个错误配置案例限定调测与生产启动的边界。
<!-- cannbot:related:end -->
