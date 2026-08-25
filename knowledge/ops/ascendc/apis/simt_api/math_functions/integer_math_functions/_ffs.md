---
type: API
title: __ffs（整数数学函数）
description: 从二进制输入数据的最低位开始，查找第一个值为1的比特位的位置，并返回该位置的索引，索引从1开始计数；如果二进制数据中没有1，则返回0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/__ffs.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __ffs

查找首位 1 的位置。从二进制输入数据的最低位开始，查找第一个值为 1 的比特位的位置并返回其索引（索引从 1 开始计数）；若数据中没有 1，则返回 0。

函数原型（重载）：int __ffs(int x)、int __ffs(long long x)、int __ffs(long x)

参数 x 为源操作数。返回二进制低位起第一个为 1 的比特位位置。x=0 时返回 0，x=1 时返回 1。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [asc_ffs（标量计算）](../../../simd_api/c_api/scalar_compute/asc_ffs.md)（`related`）：“__ffs（整数数学函数）”处理从二进制输入数据的最低位开始，查找第一个值为1的比特位的位置，并返回该位置的索引，索引从1开始计数；如果二进制数据中没有1，则返回0。；“asc_ffs（标量计算）”明确FindFirstSet接口，输入数据的二进制表示中从最低位向最高位查找第一个值为1的位，并返回其位置，如果没找到则返回-1。。实质衔接：__ffs 与 asc_ffs 都从最低位查找首个 1，但未命中返回值不同，跨编程层迁移时必须核对这一契约。
<!-- cannbot:related:end -->
