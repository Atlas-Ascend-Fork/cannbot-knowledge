---
type: API
title: asc_get_squeeze_status
description: 读取squeeze操作后保存至AR特殊寄存器的有效数据长度值，用于配合asc_squeeze_and_storeunalign接口获取已连续搬出的有效数据量。
tags:
- task.lookup
- topic.implementation.api_layer.c_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/spr/asc_get_squeeze_status.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/c_api/spr/spr.h
---

# asc_get_squeeze_status

## 功能说明

读取squeeze操作后保存至AR特殊寄存器的有效数据长度值，用于配合[asc_squeeze_and_storeunalign](../reg_compute/reg_permute_sel/asc_squeeze_and_storeunalign.md)接口获取已连续搬出的有效数据量。

## 函数原型

```cpp
__aicore__ inline int64_t asc_get_squeeze_status()
```

## 参数说明

无

## 返回值说明

返回int64_t类型的squeeze有效数据长度值。

## 流水类型

PIPE_S

## 约束说明

无

## 调用示例

无
