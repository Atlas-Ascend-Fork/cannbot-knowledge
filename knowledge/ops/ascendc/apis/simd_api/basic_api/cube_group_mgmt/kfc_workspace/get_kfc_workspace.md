---
type: API
title: GetKfcWorkspace
description: 获取用于CubeResGroupHandle消息通信区的内存地址。用户使用CubeResGroupHandle接口时，需要用此接口自主管理空间地址。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/KfcWorkspace/GetKfcWorkspace.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2]
---

# GetKfcWorkspace

获取用于 CubeResGroupHandle 消息通信区的 GM 内存地址。用户使用 CubeResGroupHandle 构造函数时需用此接口自主管理空间地址。

原型：`__aicore__ inline GM_ADDR GetKfcWorkspace()`。无参数，返回 GM_ADDR。支持 950/a2。

<!-- cannbot:related:start -->
## 相关

- [UpdateKfcWorkspace](update_kfc_workspace.md)（`related`）：更新用于 CubeResGroupHandle 消息通信区的 GM 内存地址。用户使用 CubeResGroupHandle 构造函数时需用此接口自主管理空间地址。；获取用于 CubeResGroupHandle 消息通信区的 GM 内存地址。用户使用 CubeResGroupHandle 构造函数时需用此接口自主管理空间地址。；UpdateKfcWorkspace 改写 CubeResGroupHandle 消息区的 GM 地址，GetKfcWorkspace 读取同一地址；二者构成自主管理 KfcWorkspace 状态的写入与读取生命周期。
- [构造函数与析构函数](constructor_and_destructor.md)（`related`）：创建 KfcWorkspace 对象，Kfc（kernel function call）表示核间通信调用，用于管理 CubeResGroupHandle 消息通信区的 GM 空间。；获取用于 CubeResGroupHandle 消息通信区的 GM 内存地址。用户使用 CubeResGroupHandle 构造函数时需用此接口自主管理空间地址。；构造函数建立管理核间通信 GM 空间的 KfcWorkspace 对象，GetKfcWorkspace 从同一对象取得 CubeResGroupHandle 所需地址。
<!-- cannbot:related:end -->
