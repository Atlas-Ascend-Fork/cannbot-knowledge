---
type: API
title: TQueSync
description: TQueSync类的模板参数，用于指定源流水和目标流水，目的流水等待源流水，配合SetFlag/WaitFlag实现跨硬件版本兼容的核内同步。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/TQueSync_template_params.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# TQueSync

头文件路径为："basic_api/kernel_operator_block_sync_intf.h"。

TQueSync类的模板参数用于指定源流水和目标流水，目的流水等待源流水。

参数：src(输入): 源流水。支持的流水参考硬件流水类型。；dst(输入): 目的流水。支持的流水参考硬件流水类型。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [核内同步能力概述](../../../c_api/sync/intra_core_sync_overview.md)（`related`）：TQueSync 将源/目的流水编码为模板参数并配合 SetFlag/WaitFlag，提供跨硬件版本兼容的依赖表达，补充 C API 原语的选型依据。
<!-- cannbot:related:end -->
