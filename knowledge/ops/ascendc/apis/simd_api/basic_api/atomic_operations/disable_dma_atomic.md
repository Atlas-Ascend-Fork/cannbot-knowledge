---
type: API
title: DisableDmaAtomic
description: 关闭数据搬运随路原子操作，后续搬运时GM原始数据将被新数据完全覆盖。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/atomic_operations/DisableDmaAtomic.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# DisableDmaAtomic

禁用DMA搬运时的随路原子操作。调用后，后续从UB/L0C/L1到GM的DataCopy搬运不再执行原子操作，恢复为普通覆盖写入。

函数原型：__aicore__ inline void DisableDmaAtomic()。参数：无。约束：与SetAtomicAdd/SetAtomicMax等配合使用，成对调用。头文件：basic_api/kernel_operator_atomic_intf.h。
