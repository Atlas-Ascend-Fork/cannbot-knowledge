---
type: API
title: CreateCubeResGroup
description: 快速创建CubeResGroupHandle对象，内部完成消息队列空间和同步事件分配。推荐使用该接口，避免使用CubeResGroupHandle的构造函数创建对象，出现不同对象的消息队列空间冲突、同步事件错误等情况。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/CubeResGroupHandle/CreateCubeResGroup.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2]
---

# CreateCubeResGroup

快速创建 CubeResGroupHandle 对象，内部完成消息队列空间和同步事件分配。推荐使用此接口替代构造函数，避免消息队列空间冲突和同步事件错误。

模板参数：groupID（资源组 ID）、MatmulApiType（矩阵乘 API 类型）、CallBack（回调类）、CubeMsgType（用户定义的消息结构体）。接口参数：desc（KfcWorkspace 引用）、blockStart（起始 Block 编号）、blockSize（Block 数量）、msgQueueSize（消息队列大小）、tiling（GM 上 tiling 地址）。返回 CubeResGroupHandle<CubeMsgType> 对象。支持 950/a2。

<!-- cannbot:related:start -->
## 相关

- [AllocMessage](alloc_message.md)（`related`）：《AllocMessage》处理“AIV从消息队列里申请消息空间，用于存放消息结构体，返回当前申请的消息空间的地址。消息队列的深度固定为4，申请消息空间的顺序为自上而下，然后循环。当消息队列指针指向的消息空间为FREE状态时，AllocMessage返回空间的地址，否则循环等待，直到当前空间的状态为FREE。 图1 AllocMessage示意图”。《CreateCubeResGroup》明确“快速创建CubeResGroupHandle对象，内部完成消息队列空间和同步事件分配。推荐使用该接口，避免使用CubeResGroupHandle的构造函数创建对象，出现不同对象的消息队列空间冲突、同步事件错误等情况。”，可直接用于核对AllocMessage/PostMessage/FreeMessage 生命周期、Cube 资源组句柄和 KFC workspace 合同。
- [AssignQueue](assign_queue.md)（`related`）：AssignQueue 作用于已创建且完成消息队列/事件分配的 CubeResGroupHandle，CreateCubeResGroup 是推荐的安全上游构造方式。
- [CubeResGroupHandle构造函数](cube_res_group_handle_constructor.md)（`related`）：构造函数正文建议通过 CreateCubeResGroup 统一创建 Handle，以完成队列和事件资源分配并避免直接构造冲突。
- [Cube分组管理（ISASI）](../cube_group_mgmt_isasi.md)（`related`）：CreateCubeResGroup 自动完成消息队列空间和同步事件分配，并明确优先于手工构造，可避免队列空间冲突；这是落地资源分组的关键选择约束。
- [GetResCubeGroupWorkSpaceSize](../../../../utils_api/platform_info/platform_ascend_c/get_res_cube_group_work_space_size.md)（`related`）：GetResCubeGroupWorkSpaceSize calculates the workspace that must be reserved before CreateCubeResGroup constructs the group.
- [构造函数与析构函数](../kfc_workspace/constructor_and_destructor.md)（`related`）：构造函数与析构函数 与《CreateCubeResGroup》的实质衔接是：KfcWorkspace 构造把 GM 区域交给 CubeResGroup 消息通信，Get/Update workspace 与创建资源组/handle 共同管理该地址生命周期。
- [CubeResGroupHandle](cube_res_group_handle.md)（`same_topic`）：CubeResGroupHandle 与《CreateCubeResGroup》的实质衔接是：CubeResGroupHandle 管理消息、队列、barrier 与 KFC workspace 生命周期，并约束 Cube 核执行。
- [CubeResGroupHandle](cube_res_group_handle_usage.md)（`same_topic`）：CreateCubeResGroup 只完成句柄和队列/事件资源创建，usage 给出创建后的消息分配、发送、等待和退出完整生命周期。
- [UpdateKfcWorkspace](../kfc_workspace/update_kfc_workspace.md)（`same_topic`）：UpdateKfcWorkspace 与《CreateCubeResGroup》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
<!-- cannbot:related:end -->
