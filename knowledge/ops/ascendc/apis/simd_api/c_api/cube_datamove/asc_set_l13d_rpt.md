---
type: API
title: asc_set_l13d_rpt
description: 用于设置Load3Dv2接口的repeat参数。
tags:
- task.lookup
- topic.implementation.api_layer.c_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_datamove/asc_set_l13d_rpt.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
source_headers:
- include/c_api/cube_datamove/cube_datamove.h
---

# asc_set_l13d_rpt

## 功能说明

用于设置Load3Dv2接口的repeat参数。

## 函数原型

```cpp
__aicore__ inline void asc_set_l13d_rpt(asc_load3d_v2_config& config)
```

## 参数说明

**表1** 参数说明

| 参数名  | 输入/输出 | 描述 |
| :----- | :------- | :------- |
| config | 输入 | 用于设置Load3Dv2接口的repeat参数，详细说明请参考[asc_load3d_v2_config.md](../defs/union/asc_load3d_v2_config.md)。 |

## 返回值说明

无

## 流水类型

PIPE_S

## 约束说明

- 需配合[asc_load3d_v2_config.md](../defs/union/asc_load3d_v2_config.md)使用，用于设置Load3Dv2接口的repeat参数。

## 调用示例

```cpp
asc_load3d_v2_config config;
asc_set_l13d_rpt(config); // 设置Load3D的repeat相关参数为默认值rpt_stride：0，rpt_time：1，rpt_mode：0
```