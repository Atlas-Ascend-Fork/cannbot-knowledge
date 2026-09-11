---
type: API
title: asc_get_ctrl
description: 读取CTRL寄存器（控制寄存器）特定比特位上的值。
tags:
- task.lookup
- topic.implementation.api_layer.c_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/spr/asc_get_ctrl.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
source_headers:
- include/c_api/spr/spr.h
---

# asc_get_ctrl

## 功能说明

读取CTRL寄存器（控制寄存器）特定比特位上的值。

## 函数原型

```cpp
__aicore__ inline int64_t asc_get_ctrl()
```

## 参数说明

无

## 返回值说明

CTRL寄存器的值。具体含义请参考[asc_set_ctrl](asc_set_ctrl.md)中的描述。

## 流水类型

PIPE_S

## 约束说明

无

## 调用示例

无