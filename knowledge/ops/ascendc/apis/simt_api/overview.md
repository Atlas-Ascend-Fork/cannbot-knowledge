---
type: API
title: SIMT API概述
description: SIMT API是面向AI处理器的并行计算编程接口，可以实现高效的数据并行计算。SIMT API支持两种编程模型：SIMT编程、SIMD与SIMT混合编程，用户可先阅读SIMT编程简介和SIMD与SIMT混合编程简介，以了解编程基础，后续章节将详细介绍API接口。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 概述

SIMT API 是面向 AI 处理器的并行计算编程接口，支持 SIMT 编程和 SIMD 与 SIMT 混合编程两种模型。

API 分类：同步与内存栅栏（解决数据竞争与线程同步）、原子操作（UB 或 Global Memory 原子操作）、Warp 函数（Warp 内 32 线程数据处理）、数学函数（数学运算与类型转换）、地址空间谓词/转换函数、访存函数（数据加载与缓存）、协作组（线程并行协作）、调测接口。

头文件位于 ${INSTALL_DIR}/asc/include/simt_api/，通过 #include "simt_api/xxx.h" 引用。主要头文件：asc_simt.h（聚合头文件，包含常规所需）、device_functions.h（设备函数）、device_sync_functions.h（同步）、device_atomic_functions.h（原子）、device_warp_functions.h（Warp）、math_functions.h（数学）、cooperative_groups.h（协作组）。half/half2 需 asc_fp16.h，bfloat16_t/bfloat16x2_t 需 asc_bf16.h，FP8 类型需 asc_fp8.h。若已包含 asc_simt.h 则无需单独包含各子头文件。SIMT API 属于 Kernel 侧基础接口，无需额外链接库文件。
