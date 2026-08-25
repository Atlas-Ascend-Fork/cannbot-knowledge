---
type: API
title: Nop
description: 通过输入延迟个数实现延迟若干个cycle。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/scalar_compute/Nop.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Nop

头文件路径为："basic_api/kernel_operator_utils_intf.h"。

用户输入延迟的个数，实现延迟若干个cycle。

参数：count(输入): 延迟count个cycle。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [asc_nop（内存访问函数）](../../../simt_api/memory_access_functions/asc_nop.md)（`related`）：SIMT asc_nop 与 Scalar Nop 都插入延迟，但调用空间和线程执行模型不同。
<!-- cannbot:related:end -->
