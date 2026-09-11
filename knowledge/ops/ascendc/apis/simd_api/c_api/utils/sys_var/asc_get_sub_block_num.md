---
type: API
title: asc_get_sub_block_num
description: 分离模式下，获取一个AI Core上Cube Core（AIC）或者Vector Core（AIV）的数量。
tags:
- task.lookup
- topic.implementation.api_layer.c_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/utils/sys_var/asc_get_sub_block_num.md
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

# asc_get_sub_block_num

## 功能说明

分离模式下，获取一个AI Core上Cube Core（AIC）或者Vector Core（AIV）的数量。

## 函数原型

```cpp
__aicore__ inline int64_t asc_get_sub_block_num()
```

## 参数说明

无

## 返回值说明


不同核函数（Kernel）类型下，在AIC和AIV上调用该接口的返回值如下：

**表1** 不同核函数（Kernel）类型下的返回值

|核函数（Kernel）类型|KERNEL_TYPE_AIV_ONLY|KERNEL_TYPE_AIC_ONLY|KERNEL_TYPE_MIX_AIC_1_2|KERNEL_TYPE_MIX_AIC_1_1|KERNEL_TYPE_MIX_AIC_1_0|KERNEL_TYPE_MIX_AIV_1_0|
| :------ | :------------------ | :----------------- | :-------------------- | :--------------------- | :-------------------- | :-------------------- |
|AIV      |1                    |-                   |2                      |1                       |-                      |1                      |
|AIC      |-                    |1                   |1                      |1                       |1                      |-                      |

## 流水类型

PIPE_S

## 约束说明

无

## 调用示例

无
