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
