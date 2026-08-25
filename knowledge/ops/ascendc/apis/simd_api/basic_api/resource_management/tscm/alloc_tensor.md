---
type: API
title: AllocTensor
description: 从TSCM中分配tensor，大小为InitBuffer时设置的每块内存长度，分配内容可能为随机值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TSCM/AllocTensor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AllocTensor

头文件路径为："basic_api/kernel_tpipe.h"。

从TSCM中分配tensor，tensor所占大小为InitBuffer时设置的每块内存长度。注意，分配的tensor内容并非全0，可能会是随机值。

参数：T: 待获取Tensor的数据类型，支持的类型请见LocalTensor相关描述。

仅 Ascend 950PR/Ascend 950DT 支持。
