---
type: API
title: 其他操作
description: SIMD C语言杂项接口集合，当前包含asc_init初始化接口。
tags: [task.lookup, topic.implementation.api_layer.c_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/misc/other_operations.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# 其他操作

提供 asc_init 接口，将当前 AI Core 上可能由前序算子遗留的全局状态恢复为接口约定的初始状态，避免影响当前算子计算结果。该接口仅初始化控制状态，不会清零 Global Memory、Local Memory 或用户数据。

不同产品初始化范围不同：Ascend 950PR/950DT 初始化原子累加状态、Mask 模式、CTRL 寄存器、原子操作配置、AIC Padding 值、AIV Mask 和循环次数；Atlas A3 系列仅初始化 AIV 相关状态（原子累加、Mask 模式、Mask 值）；Atlas A2 系列仅保证编译兼容。
