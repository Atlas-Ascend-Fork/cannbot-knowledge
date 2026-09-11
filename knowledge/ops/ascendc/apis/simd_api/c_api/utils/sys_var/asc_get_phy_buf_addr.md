---
type: API
title: asc_get_phy_buf_addr
description: 基于偏移量offset获取片上实际物理地址。
tags:
- task.lookup
- topic.implementation.api_layer.c_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/utils/sys_var/asc_get_phy_buf_addr.md
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

# asc_get_phy_buf_addr

## 功能说明

基于偏移量offset获取片上实际物理地址。

## 函数原型

```cpp
__aicore__ inline uint64_t asc_get_phy_buf_addr(uint64_t offset)
```

## 参数说明

**表1** 参数说明

|参数名|输入/输出|描述|
| :------ | :--- | :------------ |
|offset   |输入   |片上内存的地址偏移量，范围是0~物理内存大小。|

## 返回值说明

物理内存的地址。

## 流水类型

PIPE_S

## 约束说明

不能和[以数组方式申请内存的方法](../../general_description_and_constraints.md#以数组方式申请内存)混用。

## 调用示例

```cpp
// 假设src0，src1，dst三个操作数均包含64个half类型的数据。
uint64_t offset = 0;                                   // 首先为src0申请内存，从0开始。
__ubuf__ half* src0 = (__ubuf__ half*)asc_get_phy_buf_addr(offset);    // 获取src0的地址，通过__ubuf__关键字指定该地址指向Unified Buffer（UB）内存。
offset += 64 * sizeof(half);                           // 通过offset将src1的起始地址设置在src0之后。
__ubuf__ half* src1 = (__ubuf__ half*)asc_get_phy_buf_addr(offset);    // 获取src1的地址，通过__ubuf__关键字指定该地址指向UB内存。
offset += 64 * sizeof(half);                           // 通过offset将dst的起始地址设置在src1之后。
__ubuf__ half* dst = (__ubuf__ half*)asc_get_phy_buf_addr(offset);     // 获取dst的地址，通过__ubuf__关键字指定该地址指向UB内存。
...... // 使用src0、src1、dst中的数据进行后续计算或数据搬运操作。
```
