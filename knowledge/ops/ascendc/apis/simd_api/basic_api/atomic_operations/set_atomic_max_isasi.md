---
type: API
title: SetAtomicMax
description: 对后续搬运到GM的数据开启原子取大，将拷贝内容与GM已有值比较后写入最大值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/atomic_operations/SetAtomicMax_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SetAtomicMax

设置DMA搬运时的随路原子操作为取最大值。调用后，后续从UB/L0C/L1到GM的DataCopy搬运将对目标GM地址执行原子取最大值（旧值和新值中的最大值）。

函数原型：__aicore__ inline void SetAtomicMax<T>()。模板参数T指定数据类型。参数：无。约束：与DisableDmaAtomic配合使用；取最大值满足结合律，不存在非确定性问题。头文件：basic_api/kernel_operator_atomic_intf.h。
