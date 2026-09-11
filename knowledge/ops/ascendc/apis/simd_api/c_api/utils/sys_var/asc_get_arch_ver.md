---
type: API
title: asc_get_arch_ver
description: 获取当前AI处理器架构版本号。
tags:
- task.lookup
- topic.implementation.api_layer.c_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/utils/sys_var/asc_get_arch_ver.md
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

# asc_get_arch_ver

## 功能说明

获取当前AI处理器架构版本号。

## 函数原型

```cpp
__aicore__ inline void asc_get_arch_ver(uint32_t& core_version)
```

## 参数说明

**表1** 参数说明

| 参数名  | 输入/输出 | 描述 |
| :----- | :------- | :------- |
| core_version | 输出 | AI处理器架构版本，数据类型uint32_t。 |

## 返回值说明

无

## 流水类型

PIPE_S

## 约束说明

在调用asc_get_arch_ver接口前，需先定义core_version,调用asc_get_arch_ver接口后core_version会变成相对应架构版本号的值。

## 调用示例

```cpp
uint32_t core_version = 0;// 定义AI处理器版本
asc_get_arch_ver(core_version);
printf("core version is %u", core_version);
```
