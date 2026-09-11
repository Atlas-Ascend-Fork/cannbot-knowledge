---
type: API
title: asc_set_l3d_rpt_b
description: 用于设置接口asc_copy_l12l0a、asc_copy_l12l0b的2D格式搬运的repeat参数。
tags:
- task.lookup
- topic.implementation.api_layer.c_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_datamove/asc_set_l3d_rpt_b.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/c_api/cube_datamove/cube_datamove.h
---

# asc_set_l3d_rpt_b

## 功能说明

用于设置接口[asc_copy_l12l0a](asc_copy_l12l0a/asc_copy_l12l0a_3d_arch_3510.md)、[asc_copy_l12l0b](asc_copy_l12l0b/asc_copy_l12l0b_3d_arch_3510.md)的2D格式搬运的repeat参数。

## 函数原型

```cpp
__aicore__ inline void asc_set_l3d_rpt_b(uint64_t config)
```

## 参数说明

**表1** 参数说明

| 参数名  | 输入/输出 | 描述 |
| :----- | :------- | :------- |
| config | 输入 | 用于设置接口asc_copy_l12l0a、asc_copy_l12l0b的2D格式搬运repeat参数。比特位说明参考表2。 |

**表2** 常用重复控制寄存器比特位说明

|L3D_RPT_B比特位    |功能|
| :-------     | :---- |
| L3D_RPT_B[15:0]    | 表示重复步长    | 
| L3D_RPT_B[23:16]   | 表示在M或K方向的重复次数，默认值为1。      | 
| L3D_RPT_B[24]      | 表示重复模式 <br> - 1'b0: 在M方向重复。 <br> - 1'b1: 在K方向重复。     | 
| L3D_RPT_B[47:32]   | 表示输出矩阵在K方向上的步长，以分形为单位。     | 
| L3D_RPT_B[63:48]   | 表示输出矩阵在M方向上的起始位置，以分形为单位。      | 

## 返回值说明

无

## 流水类型

PIPE_S

## 约束说明

- 需要配合接口[asc_copy_l12l0a](asc_copy_l12l0a/asc_copy_l12l0a_3d_arch_3510.md)、[asc_copy_l12l0b](asc_copy_l12l0b/asc_copy_l12l0b_3d_arch_3510.md)使用。

## 调用示例

```cpp
uint64_t config = 0;
asc_set_l3d_rpt_b(config);
```
