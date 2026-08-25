---
type: API
title: GetSysWorkSpacePtr
description: 获取系统workspace指针。部分高阶API如Matmul需要使用系统workspace，相关接口需要传入系统workspace指针，此时可以通过该接口获取。使用系统workspace时，host侧开发者需要自行申请系统workspace的空间，其预留空间大小可以通过GetLibApiWorkSpaceSize接口获取。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/workspace/GetSysWorkSpacePtr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# GetSysWorkSpacePtr

获取系统workspace指针。部分高阶API如Matmul需要使用系统workspace，相关接口需要传入系统workspace指针，此时可以通过该接口获取。使用系统workspace时，host侧开发者需要自行申请系统workspace的空间，其预留空间大小可以通过GetLibApiWorkSpaceSize接口获取。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [507035 host tiling workspace 缺 RESERVED](../../../../../runbooks/compilation/register_none_tiling_reserved_workspace_507035.md)（`exemplifies`）：507035 host tiling workspace 缺 RESERVED 与《GetSysWorkSpacePtr》的实质衔接是：REGISTER_NONE_TILING wrapper 会先预留系统 workspace，再把用户指针偏移 RESERVED_WORKSPACE；RegisterNoneTiling、Get/SetSysWorkspace、GetUserWorkspace 与指南构成同一地址契约。
- [如何使用workspace](../../../../../guides/programming_guide/appendix/common_operations/how_to_use_workspace.md)（`explains`）：指南解释系统区、用户区的分配和 Host 预留流程，使 GetSysWorkSpacePtr 的来源、容量和使用者形成完整闭环。
- [核函数内删除Workspace相关冗余操作](../../../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/remove_workspace_redundancy.md)（`explains`）：核函数内删除Workspace相关冗余操作 与《GetSysWorkSpacePtr》的实质衔接是：workspace 已直接是用户 Workspace 时不应再 SetSysWorkSpace/GetUserWorkspace；Workspace API、使用指南和 RESERVED/预偏移案例界定何时仍需系统区与局部区。
- [GetUserWorkspace](get_user_workspace.md)（`related`）：Kernel 直调需手动设置系统 workspace 时，GetUserWorkspace 用于取得扣除系统保留区后的用户空间，避免两类指针混用。
- [UpdateKfcWorkspace](../../cube_group_mgmt/kfc_workspace/update_kfc_workspace.md)（`related`）：UpdateKfcWorkspace 与《GetSysWorkSpacePtr》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
- [SetSysWorkSpace](set_sys_work_space.md)（`same_topic`）：SetSysWorkSpace 与《GetSysWorkSpacePtr》的实质衔接是：SetSysWorkSpace 设置高阶 API 的系统区指针；Host 先用 GetLibApiWorkSpaceSize 计量，kernel 再经 GetSys/GetUserWorkspace 分区，RESERVED 故障验证偏移契约。
<!-- cannbot:related:end -->
