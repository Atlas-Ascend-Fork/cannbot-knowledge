---
type: API
title: asc_set_gm2ub_loop_size
description: 将数据从Global Memory (GM)搬运到Unified Buffer（UB）时，通过调用该接口设置数据搬运流程中的循环次数。
tags:
- task.lookup
- topic.implementation.api_layer.c_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_datamove/asc_set_gm2ub_loop_size.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/c_api/vector_datamove/vector_datamove.h
---

# asc_set_gm2ub_loop_size

## 功能说明

将数据从Global Memory (GM)搬运到Unified Buffer（UB）时，通过调用该接口设置数据搬运流程中的循环次数。

以源操作数搬运场景为例，如下图所示。

![源操作数搬运场景示例](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/SIMD-API/c_api/figures/source_operand_move_example.png)

## 函数原型

```cpp
__aicore__ inline void asc_set_gm2ub_loop_size(uint64_t loop1_size, uint64_t loop2_size)
```

## 参数说明

**表1** 参数说明

|参数名|输入/输出|描述|
|------------|------------|-----------|
| loop1_size     | 输入     | 内层循环的循环次数，取值范围为[0, 2^21)。|
| loop2_size     | 输入     | 外层循环的循环次数，取值范围为[0, 2^21)。|

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
