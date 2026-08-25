---
type: API
title: GetUserWorkspace
description: 获取用户使用的workspace指针。Kernel直调开发方式下，如果未开启HAVE_WORKSPACE编译选项，框架不会自动设置系统workspace。如果使用了Matmul
  Kernel侧接口等需要系统workspace的高阶API，kernel侧需要通过SetSysWorkSpace设置系统workspace，此时用户workspace需要通过该接口获取。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/workspace/GetUserWorkspace.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# GetUserWorkspace

获取用户使用的workspace指针。Kernel直调开发方式下，如果未开启HAVE_WORKSPACE编译选项，框架不会自动设置系统workspace。如果使用了Matmul Kernel侧接口等需要系统workspace的高阶API，kernel侧需要通过SetSysWorkSpace设置系统workspace，此时用户workspace需要通过该接口获取。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [507035 host tiling workspace 缺 RESERVED](../../../../../runbooks/compilation/register_none_tiling_reserved_workspace_507035.md)（`exemplifies`）：507035 host tiling workspace 缺 RESERVED 与《GetUserWorkspace》的实质衔接是：REGISTER_NONE_TILING wrapper 会先预留系统 workspace，再把用户指针偏移 RESERVED_WORKSPACE；RegisterNoneTiling、Get/SetSysWorkspace、GetUserWorkspace 与指南构成同一地址契约。
- [ACLNN GetWorkspaceSize 缺 L0 调用致输出全零](../../../../../runbooks/compilation/aclnn_l2_get_workspace_size_requires_l0_launcher_list.md)（`exemplifies`）：GetUserWorkspace 与《ACLNN GetWorkspaceSize 缺 L0 调用致输出全零》的实质衔接是：GetUserWorkspace 与 SetSysWorkSpace 分离用户区和系统区；workspace 指南、Matmul workspace 设置及 host staging/偏移故障说明地址从 host 到 kernel 的使用边界。
- [Host workspace 需先 CPU 暂存再 H2D](../../../../../runbooks/compilation/host_workspace_uses_cpu_staging_before_h2d.md)（`exemplifies`）：GetUserWorkspace 与《Host workspace 需先 CPU 暂存再 H2D》的实质衔接是：GetUserWorkspace 与 SetSysWorkSpace 分离用户区和系统区；workspace 指南、Matmul workspace 设置及 host staging/偏移故障说明地址从 host 到 kernel 的使用边界。
- [Matmul workspace 预偏移 totalN 回读 banned](../../../../../runbooks/precision/matmul_workspace_totaln_banned.md)（`exemplifies`）：GetUserWorkspace 与《Matmul workspace 预偏移 totalN 回读 banned》的实质衔接是：GetUserWorkspace 与 SetSysWorkSpace 分离用户区和系统区；workspace 指南、Matmul workspace 设置及 host staging/偏移故障说明地址从 host 到 kernel 的使用边界。
- [如何使用workspace](../../../../../guides/programming_guide/appendix/common_operations/how_to_use_workspace.md)（`explains`）：GetUserWorkspace 与《如何使用workspace》的实质衔接是：GetUserWorkspace 与 SetSysWorkSpace 分离用户区和系统区；workspace 指南、Matmul workspace 设置及 host staging/偏移故障说明地址从 host 到 kernel 的使用边界。
- [核函数内删除Workspace相关冗余操作](../../../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/remove_workspace_redundancy.md)（`explains`）：核函数内删除Workspace相关冗余操作 与《GetUserWorkspace》的实质衔接是：workspace 已直接是用户 Workspace 时不应再 SetSysWorkSpace/GetUserWorkspace；Workspace API、使用指南和 RESERVED/预偏移案例界定何时仍需系统区与局部区。
- [GetSysWorkSpacePtr](get_sys_work_space_ptr.md)（`related`）：Kernel 直调需手动设置系统 workspace 时，GetUserWorkspace 用于取得扣除系统保留区后的用户空间，避免两类指针混用。
- [SetLocalWorkspace](../../../adv_api/cube_compute/matmul_kernel/set_local_workspace.md)（`related`）：GetUserWorkspace 与《SetLocalWorkspace》的实质衔接是：GetUserWorkspace 与 SetSysWorkSpace 分离用户区和系统区；workspace 指南、Matmul workspace 设置及 host staging/偏移故障说明地址从 host 到 kernel 的使用边界。
- [SetWorkspace](../../../adv_api/cube_compute/matmul_kernel/set_workspace.md)（`related`）：GetUserWorkspace 与《SetWorkspace》的实质衔接是：GetUserWorkspace 与 SetSysWorkSpace 分离用户区和系统区；workspace 指南、Matmul workspace 设置及 host staging/偏移故障说明地址从 host 到 kernel 的使用边界。
- [UpdateKfcWorkspace](../../cube_group_mgmt/kfc_workspace/update_kfc_workspace.md)（`related`）：UpdateKfcWorkspace 与《GetUserWorkspace》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
- [SetSysWorkSpace](set_sys_work_space.md)（`same_topic`）：GetUserWorkspace 与《SetSysWorkSpace》的实质衔接是：GetUserWorkspace 与 SetSysWorkSpace 分离用户区和系统区；workspace 指南、Matmul workspace 设置及 host staging/偏移故障说明地址从 host 到 kernel 的使用边界。
- [Workspace](workspace.md)（`same_topic`）：GetUserWorkspace 与《Workspace》的实质衔接是：GetUserWorkspace 与 SetSysWorkSpace 分离用户区和系统区；workspace 指南、Matmul workspace 设置及 host staging/偏移故障说明地址从 host 到 kernel 的使用边界。
<!-- cannbot:related:end -->
