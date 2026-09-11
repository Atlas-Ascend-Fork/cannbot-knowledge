---
type: API
title: asc_set_l13d_fmatrix
description: 设置Feature map属性描述，用于在调用asc_copy_l12l0a/asc_copy_l12l0b的3D格式搬运接口时配置填充数值。
  仅当asc_copy_l12l0a/asc_copy_l12l0b接口的f_matrix_ctrl参数指示从左矩阵获取FeatureMap的属性时使用本接口设置Feature
  map属性描述，否则使用asc_set_l13d_fmatrix_b接口。
tags:
- task.lookup
- topic.implementation.api_layer.c_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_datamove/asc_set_l13d_fmatrix.md
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

# asc_set_l13d_fmatrix

## 功能说明

设置Feature map属性描述，用于在调用[asc_copy_l12l0a](asc_copy_l12l0a/index.md)/[asc_copy_l12l0b](asc_copy_l12l0b/index.md)的3D格式搬运接口时配置填充数值。
仅当asc_copy_l12l0a/asc_copy_l12l0b接口的f_matrix_ctrl参数指示从左矩阵获取FeatureMap的属性时使用本接口设置Feature map属性描述，否则使用asc_set_l13d_fmatrix_b接口。

## 函数原型

```cpp
__aicore__ inline void asc_set_l13d_fmatrix(asc_l13d_fmatrix_config& config)
```

## 参数说明

**表1** 参数说明

| 参数名  | 输入/输出 | 描述 |
| :----- | :------- | :------- |
| config | 输入 | 用于设置asc_copy_l12l0a/asc_copy_l12l0b的3D格式搬运接口的Feature map属性参数，详细说明请参考[asc_l13d_fmatrix_config](../defs/union/asc_l13d_fmatrix_config.md)。 |

## 返回值说明

无

## 流水类型

PIPE_S

## 约束说明

无

## 调用示例

```cpp
asc_l13d_fmatrix_config config;
config.l1_height = 1;
config.l1_width = 2;
config.padding_left_size = 3;
config.padding_right_size = 4;
config.padding_top_size = 5;
config.padding_bottom_size = 6;
asc_set_l13d_fmatrix(config);
```
