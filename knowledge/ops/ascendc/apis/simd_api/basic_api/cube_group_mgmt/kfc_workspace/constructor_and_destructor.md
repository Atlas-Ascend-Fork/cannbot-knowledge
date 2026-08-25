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

- [CreateCubeResGroup](../cube_res_group_handle/create_cube_res_group.md)（`related`）：构造函数与析构函数 与《CreateCubeResGroup》的实质衔接是：KfcWorkspace 构造把 GM 区域交给 CubeResGroup 消息通信，Get/Update workspace 与创建资源组/handle 共同管理该地址生命周期。
- [CubeResGroupHandle](../cube_res_group_handle/cube_res_group_handle.md)（`related`）：构造函数与析构函数 与《CubeResGroupHandle》的实质衔接是：KfcWorkspace 构造把 GM 区域交给 CubeResGroup 消息通信，Get/Update workspace 与创建资源组/handle 共同管理该地址生命周期。
- [GetKfcWorkspace](get_kfc_workspace.md)（`same_topic`）：GetKfcWorkspace 与《构造函数与析构函数》的实质衔接是：GetKfcWorkspace 返回 CubeResGroup 消息区 GM 地址；KfcWorkspace 构造/Get/Update 和资源组 handle 共同管理该地址的生命周期。
- [KfcWorkspace](kfc_workspace.md)（`same_topic`）：构造函数与析构函数 与《KfcWorkspace》的实质衔接是：KfcWorkspace 构造把 GM 区域交给 CubeResGroup 消息通信，Get/Update workspace 与创建资源组/handle 共同管理该地址生命周期。
- [UpdateKfcWorkspace](update_kfc_workspace.md)（`same_topic`）：UpdateKfcWorkspace 与《构造函数与析构函数》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
<!-- cannbot:related:end -->
