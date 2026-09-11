---
type: API
title: AscSyncVec
description: 针对PIPE_V流水线执行同步操作。无入参函数原型已废弃，请使用asc_sync执行所有流水线的同步。
tags:
- task.lookup
- topic.implementation.synchronization
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sync/asc_sync_vec.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
---

# asc_sync_vec

## 功能说明

**无入参函数原型`asc_sync_vec()`接口已废弃，请使用[asc_sync](asc_sync.md)执行针对所有流水线的同步操作。**

针对PIPE_V流水线执行同步操作。

## 函数原型

```cpp
__aicore__ inline void asc_sync_vec(int id)
__aicore__ inline void asc_sync_vec()
```

## 参数说明

| 参数名 | 输入/输出 | 描述 |
| :--- | :--- | :--- |
| id | 输入 | 同步ID。 |

## 返回值说明

无

## 流水类型

PIPE_S

## 约束说明

同步ID的取值范围为：0-7。

## 调用示例

```cpp
// 本例中total_length指参与计算的数据总长度。src0_gm，src1_gm，dst_gm是外部输入的float类型的源操作数、目的操作数，指向GM内存空间。
constexpr uint32_t total_length = 128;
__ubuf__ float src0[total_length];
__ubuf__ float src1[total_length];
__ubuf__ float dst[total_length];

asc_copy_gm2ub(src0, src0_gm, total_length * sizeof(float));
asc_copy_gm2ub(src1, src1_gm, total_length * sizeof(float));

// 同步操作：前置操作完成后才能启动后续操作。
asc_sync();

asc_add(dst, src1, src0, total_length);

// 同步操作：矢量计算操作（asc_add, PIPE_V流水）完成后才能启动后续操作。
asc_sync_vec(0);

asc_copy_ub2gm(dst_gm, dst, total_length * sizeof(float));
```
