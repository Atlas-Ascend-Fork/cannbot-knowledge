---
type: API
title: asc_get_vf_len
description: 获取Tensor位宽VL（Vector Length）的大小。
tags:
- task.lookup
- topic.implementation.api_layer.c_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/utils/sys_var/asc_get_vf_len.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/c_api/utils/sys_var.h
---

# asc_get_vf_len

## 功能说明

获取Tensor位宽VL（Vector Length）的大小。

## 函数原型

```cpp
__aicore__ inline constexpr int64_t asc_get_vf_len()
```

## 参数说明

无

## 返回值说明

位宽VL（Vector Length）的大小。

## 流水类型

PIPE_S

## 约束说明

无

## 调用示例

```cpp
int64_t len = asc_get_vf_len();
```
