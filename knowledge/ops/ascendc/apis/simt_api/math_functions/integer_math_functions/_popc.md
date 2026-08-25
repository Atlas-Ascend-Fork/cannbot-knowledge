---
type: API
title: __popc（整数数学函数）
description: 统计输入数据从二进制的高位到低位比特位为1的数量。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/__popc.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __popc

位计数函数（population count）。统计输入数据二进制中比特位为 1 的数量。

函数原型（重载）：int __popc(unsigned int x)、int __popc(unsigned long long x)、int __popc(unsigned long x)

参数 x 为源操作数。返回二进制中 1 的位数。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [asc_popc（标量计算）](../../../simd_api/c_api/scalar_compute/asc_popc.md)（`same_topic`）：焦点处理popc 位计数在 SIMT 与 C 标量 API 的等价入口；asc_popc（标量计算）正文说明“获取一个uint64_t类型数字的二进制中1的个数”。候选执行同样的置位比特计数，只改变 API 层和输入位宽。
<!-- cannbot:related:end -->
