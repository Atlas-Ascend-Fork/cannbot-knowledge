---
type: API
title: 内存空间限定符
description: 在SIMT编程中使用内存空间限定符__ubuf__来表示动、静态内存，静态内存的大小在编译期是确定的，动态内存的大小在核函数启动时确定。
tags: [task.lookup, topic.implementation.api_layer.simt_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMT_programming_intro/extended_syntax/memory_space_qualifier.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 内存空间限定符

在 SIMT 编程中使用内存空间限定符 __ubuf__ 表示 Unified Buffer 中的动、静态内存。静态内存大小在编译期确定，通过数组分配（如 __ubuf__ half staticBuf[1024]）；动态内存大小在核函数启动时确定，通过 extern 数组声明（如 extern __ubuf__ half dynamicBuf[]），实际大小在核函数启动时配置。

<!-- cannbot:related:start -->
## 相关

- [纯 SIMT kernel 形参 __gm__ 导致编译失败](../../../../runbooks/compilation/pure_simt_parameters_do_not_use_gm_qualifier.md)（`exemplifies`）：焦点说明 __ubuf__ 用于声明 UB 静态/动态存储；故障卡给出相邻但不同的边界：纯 SIMT kernel 形参不能照搬混合模式 __gm__，否则宏展开为非法 device attribute。
- [内存层级（AI Core SIMT编程）](../../../../guides/programming_guide/programming_model/ai_core_simt_programming/memory_hierarchy.md)（`explains`）：焦点处理SIMT 内存层级与地址空间、同步可见性；内存空间限定符正文界定“在SIMT编程中使用内存空间限定符__ubuf__来表示动、静态内存，静态内存的大小在编译期是确定的，动态内存的大小在核函数启动时确定”。候选给出 SIMT 线程/硬件层级、地址空间限定符和 fence/sync 的可见性边界。
- [核函数配置](kernel_function_config.md)（`related`）：《核函数配置》的任务是“核函数是SIMT编程的Device侧入口函数，负责协调整个算子的执行流程。函数定义语法为：”。《内存空间限定符》具体提供“在SIMT编程中使用内存空间限定符__ubuf__来表示动、静态内存，静态内存的大小在编译期是确定的，动态内存的大小在核函数启动时确定。”，它直接用于SIMT Kernel 入口的执行/内存限定符、内置变量和 launch 头文件。
<!-- cannbot:related:end -->
