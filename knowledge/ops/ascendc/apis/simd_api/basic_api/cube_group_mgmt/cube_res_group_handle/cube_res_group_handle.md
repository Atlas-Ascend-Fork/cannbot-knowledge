---
type: API
title: CubeResGroupHandle
description: CubeResGroupHandle 接口集，提供 Cube 资源分组管理能力，含构造函数、CreateCubeResGroup、AssignQueue、PostMessage 等。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/CubeResGroupHandle/CubeResGroupHandle.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2]
---

# CubeResGroupHandle

Cube 资源分组管理句柄，用于在 ISASI Cube 计算中对资源进行分组与消息调度。通过 CreateCubeResGroup 创建分组，配合 AssignQueue、AllocMessage、PostMessage、PostFakeMsg、Wait、FreeMessage 实现消息的分配、发送、等待与释放；SetQuit、SetSkipMsg 用于退出与跳过控制。适用于多任务并发调度场景，需先完成使用说明中要求的初始化流程。

<!-- cannbot:related:start -->
## 相关

- [AllocMessage](alloc_message.md)（`related`）：《AllocMessage》处理“AIV从消息队列里申请消息空间，用于存放消息结构体，返回当前申请的消息空间的地址。消息队列的深度固定为4，申请消息空间的顺序为自上而下，然后循环。当消息队列指针指向的消息空间为FREE状态时，AllocMessage返回空间的地址，否则循环等待，直到当前空间的状态为FREE。 图1 AllocMessage示意图”。《CubeResGroupHandle》明确“CubeResGroupHandle 接口集，提供 Cube 资源分组管理能力，含构造函数、CreateCubeResGroup、AssignQueue、PostMessage 等。”，可直接用于核对AllocMessage/PostMessage/FreeMessage 生命周期、Cube 资源组句柄和 KFC workspace 合同。
- [GetResCubeGroupWorkSpaceSize](../../../../utils_api/platform_info/platform_ascend_c/get_res_cube_group_work_space_size.md)（`related`）：CubeResGroupHandle 与《GetResCubeGroupWorkSpaceSize》的实质衔接是：CubeResGroupHandle 管理消息、队列、barrier 与 KFC workspace 生命周期，并约束 Cube 核执行。
- [构造函数与析构函数](../kfc_workspace/constructor_and_destructor.md)（`related`）：构造函数与析构函数 与《CubeResGroupHandle》的实质衔接是：KfcWorkspace 构造把 GM 区域交给 CubeResGroup 消息通信，Get/Update workspace 与创建资源组/handle 共同管理该地址生命周期。
- [CreateCubeResGroup](create_cube_res_group.md)（`same_topic`）：CubeResGroupHandle 与《CreateCubeResGroup》的实质衔接是：CubeResGroupHandle 管理消息、队列、barrier 与 KFC workspace 生命周期，并约束 Cube 核执行。
- [CubeResGroupHandle](cube_res_group_handle_usage.md)（`same_topic`）：CubeResGroupHandle 与《CubeResGroupHandle》的实质衔接是：CubeResGroupHandle 管理消息、队列、barrier 与 KFC workspace 生命周期，并约束 Cube 核执行。
- [FreeMessage](free_message.md)（`same_topic`）：FreeMessage 与《CubeResGroupHandle》的实质衔接是：FreeMessage 释放由 AllocMessage 取得并经 PostMessage 流转的消息，CubeResGroupHandle 使用说明给出完整状态生命周期。
- [GetKfcWorkspace](../kfc_workspace/get_kfc_workspace.md)（`same_topic`）：GetKfcWorkspace 与《CubeResGroupHandle》的实质衔接是：GetKfcWorkspace 返回 CubeResGroup 消息区 GM 地址；KfcWorkspace 构造/Get/Update 和资源组 handle 共同管理该地址的生命周期。
- [SetQuit](set_quit.md)（`same_topic`）：SetQuit 与《CubeResGroupHandle》的实质衔接是：SetQuit 是 CubeResGroupHandle 消息循环的退出信号，usage 与 Wait 解释信号写入后的消费和收尾。
- [UpdateKfcWorkspace](../kfc_workspace/update_kfc_workspace.md)（`same_topic`）：UpdateKfcWorkspace 与《CubeResGroupHandle》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
<!-- cannbot:related:end -->
