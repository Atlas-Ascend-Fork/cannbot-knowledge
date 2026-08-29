---
type: API
title: 构造函数与析构函数
description: 用于创建KfcWorkspace对象，Kfc全称为kernel function call，表示核间通信调用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/KfcWorkspace/constructor_and_destructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2]
---

# 构造函数与析构函数

创建 KfcWorkspace 对象，Kfc（kernel function call）表示核间通信调用，用于管理 CubeResGroupHandle 消息通信区的 GM 空间。

原型：`KfcWorkspace(GM_ADDR workspace)` 构造，`~KfcWorkspace()` 析构。参数 workspace 为 GM 工作空间地址。支持 950/a2。

<!-- cannbot:related:start -->
## 相关

- [GetKfcWorkspace](get_kfc_workspace.md)（`related`）：创建 KfcWorkspace 对象，Kfc（kernel function call）表示核间通信调用，用于管理 CubeResGroupHandle 消息通信区的 GM 空间。；获取用于 CubeResGroupHandle 消息通信区的 GM 内存地址。用户使用 CubeResGroupHandle 构造函数时需用此接口自主管理空间地址。；构造函数建立管理核间通信 GM 空间的 KfcWorkspace 对象，GetKfcWorkspace 从同一对象取得 CubeResGroupHandle 所需地址。
<!-- cannbot:related:end -->
