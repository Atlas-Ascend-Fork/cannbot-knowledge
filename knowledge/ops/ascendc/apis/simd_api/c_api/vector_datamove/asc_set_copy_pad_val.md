---
type: API
title: asc_set_copy_pad_val
description: 和asc_copy_gm2ub_align接口配合使用，设置连续搬运数据块左右两侧需要填补的数据值。
tags:
- task.lookup
- topic.implementation.api_layer.c_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_datamove/asc_set_copy_pad_val.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
source_headers:
- include/c_api/vector_datamove/vector_datamove.h
---

# asc_set_copy_pad_val

## 功能说明

和asc_copy_gm2ub_align接口配合使用，设置连续搬运数据块左右两侧需要填补的数据值。



对于Ascend 950PR/Ascend 950DT产品：
- 该接口仅对asc_copy_gm2ub_align接口有效。
- fp8_e8m0_t、fp8_e5m2_t、fp8_e4m3fn_t、fp4x2_e2m1_t、fp4x2_e1m2_t、hifloat8_t类型的数据需转换成int8_t类型后再调用本接口。


## 函数原型

```cpp
__aicore__ inline void asc_set_copy_pad_val(int8_t pad_value)
__aicore__ inline void asc_set_copy_pad_val(uint8_t pad_value)
__aicore__ inline void asc_set_copy_pad_val(int16_t pad_value)
__aicore__ inline void asc_set_copy_pad_val(uint16_t pad_value)
__aicore__ inline void asc_set_copy_pad_val(half pad_value)
__aicore__ inline void asc_set_copy_pad_val(bfloat16_t pad_value)
__aicore__ inline void asc_set_copy_pad_val(int32_t pad_value)
__aicore__ inline void asc_set_copy_pad_val(uint32_t pad_value)
__aicore__ inline void asc_set_copy_pad_val(float pad_value)
```

## 参数说明

**表1** 参数说明

|参数名|输入/输出|描述|
|------------|------------|-----------|
| pad_value     | 输入     | 需要填补的数据值。|

## 返回值说明

无

## 流水类型

PIPE_S

## 约束说明

无

## 调用示例

```cpp
// src是外部输入的int8_t类型的GM地址。
__ubuf__ int8_t dst[128];

asc_set_copy_pad_val(0);
// 在搬运过程中，每个数据块左右两侧各补充8个int8_t的数据，补充的数据值为0。
asc_copy_gm2ub_align(dst, src, 2, 48 * sizeof(int8_t), 8, 8, true, asc_load_l2_cache_mode::NORMAL_FIRST_VICTIM, 48 * sizeof(int8_t), 64 * sizeof(int8_t));
```
