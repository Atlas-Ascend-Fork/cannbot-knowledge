---
type: API
title: asc_datacache_preload
description: 从GM地址预加载数据到Data Cache，每次调用预加载一个Cache Line大小的数据。
tags: [task.lookup, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cache_ctrl/asc_datacache_preload.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# asc_datacache_preload

从源地址所在的特定GM地址预加载数据到Data Cache中，每次调用只能预加载一个Cache Line大小的数据。

参数：address(输入): 源操作数的起始地址。；offset(输入): 在源操作数上偏移offset大小开始加载数据，单位为Bytes。

约束：频繁调用此接口可能会导致保留栈拥塞，此时，该接口将被视为NOP指令，阻塞Scalar流水。因此不建议频繁调用此接口。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。
