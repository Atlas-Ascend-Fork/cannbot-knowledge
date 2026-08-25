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

- [Host workspace 需先 CPU 暂存再 H2D](../../../../../runbooks/compilation/host_workspace_uses_cpu_staging_before_h2d.md)（`exemplifies`）：UpdateKfcWorkspace 与《Host workspace 需先 CPU 暂存再 H2D》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
- [如何使用workspace](../../../../../guides/programming_guide/appendix/common_operations/how_to_use_workspace.md)（`explains`）：UpdateKfcWorkspace 与《如何使用workspace》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
- [AllocMessage](../cube_res_group_handle/alloc_message.md)（`related`）：《AllocMessage》处理“AIV从消息队列里申请消息空间，用于存放消息结构体，返回当前申请的消息空间的地址。消息队列的深度固定为4，申请消息空间的顺序为自上而下，然后循环。当消息队列指针指向的消息空间为FREE状态时，AllocMessage返回空间的地址，否则循环等待，直到当前空间的状态为FREE。 图1 AllocMessage示意图”。《UpdateKfcWorkspace》明确“更新用于CubeResGroupHandle消息通信区的内存地址。用户使用CubeResGroupHandle接口时，需要用此接口自主管理空间地址。”，可直接用于核对AllocMessage/PostMessage/FreeMessage 生命周期、Cube 资源组句柄和 KFC workspace 合同。
- [GetSysWorkSpacePtr](../../resource_management/workspace/get_sys_work_space_ptr.md)（`related`）：UpdateKfcWorkspace 与《GetSysWorkSpacePtr》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
- [GetUserWorkspace](../../resource_management/workspace/get_user_workspace.md)（`related`）：UpdateKfcWorkspace 与《GetUserWorkspace》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
- [SetSysWorkSpace](../../resource_management/workspace/set_sys_work_space.md)（`related`）：UpdateKfcWorkspace 与《SetSysWorkSpace》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
- [Workspace](../../resource_management/workspace/workspace.md)（`related`）：UpdateKfcWorkspace 与《Workspace》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
- [CreateCubeResGroup](../cube_res_group_handle/create_cube_res_group.md)（`same_topic`）：UpdateKfcWorkspace 与《CreateCubeResGroup》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
- [CubeResGroupHandle](../cube_res_group_handle/cube_res_group_handle.md)（`same_topic`）：UpdateKfcWorkspace 与《CubeResGroupHandle》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
- [CubeResGroupHandle](../cube_res_group_handle/cube_res_group_handle_usage.md)（`same_topic`）：UpdateKfcWorkspace 与《CubeResGroupHandle》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
- [CubeResGroupHandle构造函数](../cube_res_group_handle/cube_res_group_handle_constructor.md)（`same_topic`）：UpdateKfcWorkspace 与《CubeResGroupHandle构造函数》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
- [GetKfcWorkspace](get_kfc_workspace.md)（`same_topic`）：UpdateKfcWorkspace 与《GetKfcWorkspace》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
- [KfcWorkspace](kfc_workspace.md)（`same_topic`）：UpdateKfcWorkspace 与《KfcWorkspace》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
- [构造函数与析构函数](constructor_and_destructor.md)（`same_topic`）：UpdateKfcWorkspace 与《构造函数与析构函数》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
<!-- cannbot:related:end -->
