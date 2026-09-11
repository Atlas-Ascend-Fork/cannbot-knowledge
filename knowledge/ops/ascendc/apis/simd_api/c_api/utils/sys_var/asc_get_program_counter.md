---
type: API
title: asc_get_program_counter
description: 获取程序计数器的指针，程序计数器用于记录当前程序执行的位置。
tags:
- task.lookup
- topic.implementation.api_layer.c_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/utils/sys_var/asc_get_program_counter.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
source_headers:
- include/c_api/utils/sys_var.h
---

# asc_get_program_counter

## 功能说明

获取程序计数器的指针，程序计数器用于记录当前程序执行的位置。

## 函数原型

```cpp
__aicore__ inline int64_t asc_get_program_counter()
```

## 参数说明

无

## 返回值说明

返回int64_t类型的程序计数器指针。

## 流水类型

PIPE_S

## 约束说明

无

## 调用示例

```cpp
asc_get_program_counter();
```