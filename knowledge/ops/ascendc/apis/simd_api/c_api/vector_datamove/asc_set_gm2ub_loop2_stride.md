---
type: API
title: asc_set_gm2ub_loop2_stride
description: 将数据从Global Memory (GM)搬运到Unified Buffer（UB）时，通过调用该接口设置外层循环中相邻迭代数据块间的间隔。
tags:
- task.lookup
- topic.implementation.api_layer.c_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_datamove/asc_set_gm2ub_loop2_stride.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/c_api/vector_datamove/vector_datamove.h
---

# asc_set_gm2ub_loop2_stride

## 功能说明

将数据从Global Memory (GM)搬运到Unified Buffer（UB）时，通过调用该接口设置外层循环中相邻迭代数据块间的间隔。

以源操作数搬运场景为例，如下图所示。

![源操作数搬运场景示例](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/SIMD-API/c_api/figures/source_operand_move_example.png)

## 函数原型

```cpp
__aicore__ inline void asc_set_gm2ub_loop2_stride(uint64_t loop2_src_stride, uint64_t loop2_dst_stride)
```

## 参数说明

**表1** 参数说明

|参数名|输入/输出|描述|
|------------|------------|-----------|
| loop2_src_stride     | 输入     | 外层循环中相邻迭代源操作数的数据块间的间隔，单位为Byte，取值范围为[0, 2^40)。|
| loop2_dst_stride     | 输入     | 外层循环中相邻迭代目标操作数的数据块间的间隔，单位为Byte，取值范围为[0, 2^21)，且必须32B对齐。|

## 返回值说明

无

## 流水类型

PIPE_S

## 约束说明

每次设置循环相关参数后，需要进行寄存器的复位（循环次数设置为1），否则会影响下一次搬运的使用。

## 调用示例

```cpp
asc_set_gm2ub_loop_size(2, 2);
asc_set_gm2ub_loop1_stride(96, 128);
asc_set_gm2ub_loop2_stride(192, 288);
asc_copy_gm2ub_align(dst, src, 2, 48 * sizeof(int8_t), 0, 0, false, asc_load_l2_cache_mode::NORMAL_FIRST_VICTIM, 48, 48);
asc_set_gm2ub_loop_size(1, 1);
```
