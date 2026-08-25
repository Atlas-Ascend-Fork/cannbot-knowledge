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

- [AllocMessage](../cube_res_group_handle/alloc_message.md)（`related`）：《AllocMessage》处理“AIV从消息队列里申请消息空间，用于存放消息结构体，返回当前申请的消息空间的地址。消息队列的深度固定为4，申请消息空间的顺序为自上而下，然后循环。当消息队列指针指向的消息空间为FREE状态时，AllocMessage返回空间的地址，否则循环等待，直到当前空间的状态为FREE。 图1 AllocMessage示意图”。《GetKfcWorkspace》明确“获取用于CubeResGroupHandle消息通信区的内存地址。用户使用CubeResGroupHandle接口时，需要用此接口自主管理空间地址。”，可直接用于核对AllocMessage/PostMessage/FreeMessage 生命周期、Cube 资源组句柄和 KFC workspace 合同。
- [CubeResGroupHandle](../cube_res_group_handle/cube_res_group_handle.md)（`same_topic`）：GetKfcWorkspace 与《CubeResGroupHandle》的实质衔接是：GetKfcWorkspace 返回 CubeResGroup 消息区 GM 地址；KfcWorkspace 构造/Get/Update 和资源组 handle 共同管理该地址的生命周期。
- [CubeResGroupHandle构造函数](../cube_res_group_handle/cube_res_group_handle_constructor.md)（`same_topic`）：GetKfcWorkspace 与《CubeResGroupHandle构造函数》的实质衔接是：GetKfcWorkspace 返回 CubeResGroup 消息区 GM 地址；KfcWorkspace 构造/Get/Update 和资源组 handle 共同管理该地址的生命周期。
- [KfcWorkspace](kfc_workspace.md)（`same_topic`）：GetKfcWorkspace 与《KfcWorkspace》的实质衔接是：GetKfcWorkspace 返回 CubeResGroup 消息区 GM 地址；KfcWorkspace 构造/Get/Update 和资源组 handle 共同管理该地址的生命周期。
- [UpdateKfcWorkspace](update_kfc_workspace.md)（`same_topic`）：UpdateKfcWorkspace 与《GetKfcWorkspace》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
- [构造函数与析构函数](constructor_and_destructor.md)（`same_topic`）：GetKfcWorkspace 与《构造函数与析构函数》的实质衔接是：GetKfcWorkspace 返回 CubeResGroup 消息区 GM 地址；KfcWorkspace 构造/Get/Update 和资源组 handle 共同管理该地址的生命周期。
<!-- cannbot:related:end -->
