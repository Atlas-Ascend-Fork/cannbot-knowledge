---
type: API
title: UpdateKfcWorkspace
description: 更新用于CubeResGroupHandle消息通信区的内存地址。用户使用CubeResGroupHandle接口时，需要用此接口自主管理空间地址。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/KfcWorkspace/UpdateKfcWorkspace.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2]
---

# UpdateKfcWorkspace

更新用于 CubeResGroupHandle 消息通信区的 GM 内存地址。用户使用 CubeResGroupHandle 构造函数时需用此接口自主管理空间地址。

原型：`__aicore__ inline void UpdateKfcWorkspace(uint32_t offset)`。参数 offset 为地址偏移量。支持 950/a2。

<!-- cannbot:related:start -->
## 相关

- [GetKfcWorkspace](get_kfc_workspace.md)（`related`）：更新用于 CubeResGroupHandle 消息通信区的 GM 内存地址。用户使用 CubeResGroupHandle 构造函数时需用此接口自主管理空间地址。；获取用于 CubeResGroupHandle 消息通信区的 GM 内存地址。用户使用 CubeResGroupHandle 构造函数时需用此接口自主管理空间地址。；UpdateKfcWorkspace 改写 CubeResGroupHandle 消息区的 GM 地址，GetKfcWorkspace 读取同一地址；二者构成自主管理 KfcWorkspace 状态的写入与读取生命周期。
<!-- cannbot:related:end -->
