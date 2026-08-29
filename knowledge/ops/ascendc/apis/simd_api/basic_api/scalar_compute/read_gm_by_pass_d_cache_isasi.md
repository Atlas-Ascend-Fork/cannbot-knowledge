---
type: API
title: ReadGmByPassDCache
description: 不经过DCache从GM地址读取数据。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/scalar_compute/ReadGmByPassDCache_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# ReadGmByPassDCache

头文件路径为："basic_api/kernel_operator_scalar_intf.h"。

不经过DCache从GM地址上读数据。

参数：T: 操作数的数据类型。；addr(输入): 源GM地址。

支持数据类型：支持的数据类型为int8_t、uint8_t、int16_t、uint16_t、int32_t、uint32_t、int64_t、uint64_t。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。
