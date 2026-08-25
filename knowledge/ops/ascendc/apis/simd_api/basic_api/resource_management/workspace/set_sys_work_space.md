---
type: API
title: SetSysWorkSpace
description: 设置系统workspace指针，供Matmul Kernel等高阶API使用；工程化或kernel直调方式由框架自动设置，其他场景需开发者手动调用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/workspace/SetSysWorkSpace.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# SetSysWorkSpace

框架需要使用的workspace称之为系统workspace。Matmul Kernel侧接口等高阶API需要系统workspace，所以在使用该类API时，需要调用该接口，设置系统workspace的指针。采用工程化算子开发方式或者kernel直调方式（开启HAVE_WORKSPACE编译选项）时，不需要开发者手动设置，框架会自动设置。其他场景下，需要开发者调用SetSysWorkSpace进行设置。

在kernel侧调用该接口前，需要在host侧调用GetLibApiWorkSpaceSize获取系统workspace的大小，并在host侧设置workspacesize大小。样例

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [507035 host tiling workspace 缺 RESERVED](../../../../../runbooks/compilation/register_none_tiling_reserved_workspace_507035.md)（`exemplifies`）：507035 host tiling workspace 缺 RESERVED 与《SetSysWorkSpace》的实质衔接是：REGISTER_NONE_TILING wrapper 会先预留系统 workspace，再把用户指针偏移 RESERVED_WORKSPACE；RegisterNoneTiling、Get/SetSysWorkspace、GetUserWorkspace 与指南构成同一地址契约。
- [如何使用workspace](../../../../../guides/programming_guide/appendix/common_operations/how_to_use_workspace.md)（`explains`）：SetSysWorkSpace 与《如何使用workspace》的实质衔接是：SetSysWorkSpace 设置高阶 API 的系统区指针；Host 先用 GetLibApiWorkSpaceSize 计量，kernel 再经 GetSys/GetUserWorkspace 分区，RESERVED 故障验证偏移契约。
- [核函数内删除Workspace相关冗余操作](../../../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/remove_workspace_redundancy.md)（`explains`）：SetSysWorkSpace 与《核函数内删除Workspace相关冗余操作》的实质衔接是：SetSysWorkSpace 设置高阶 API 的系统区指针；Host 先用 GetLibApiWorkSpaceSize 计量，kernel 再经 GetSys/GetUserWorkspace 分区，RESERVED 故障验证偏移契约。
- [UpdateKfcWorkspace](../../cube_group_mgmt/kfc_workspace/update_kfc_workspace.md)（`related`）：UpdateKfcWorkspace 与《SetSysWorkSpace》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
- [GetLibApiWorkSpaceSize](../../../../utils_api/platform_info/platform_ascend_c/get_lib_api_work_space_size.md)（`same_topic`）：SetSysWorkSpace 与《GetLibApiWorkSpaceSize》的实质衔接是：SetSysWorkSpace 设置高阶 API 的系统区指针；Host 先用 GetLibApiWorkSpaceSize 计量，kernel 再经 GetSys/GetUserWorkspace 分区，RESERVED 故障验证偏移契约。
- [GetSysWorkSpacePtr](get_sys_work_space_ptr.md)（`same_topic`）：SetSysWorkSpace 与《GetSysWorkSpacePtr》的实质衔接是：SetSysWorkSpace 设置高阶 API 的系统区指针；Host 先用 GetLibApiWorkSpaceSize 计量，kernel 再经 GetSys/GetUserWorkspace 分区，RESERVED 故障验证偏移契约。
- [GetUserWorkspace](get_user_workspace.md)（`same_topic`）：GetUserWorkspace 与《SetSysWorkSpace》的实质衔接是：GetUserWorkspace 与 SetSysWorkSpace 分离用户区和系统区；workspace 指南、Matmul workspace 设置及 host staging/偏移故障说明地址从 host 到 kernel 的使用边界。
- [Workspace](workspace.md)（`same_topic`）：SetSysWorkSpace 与《Workspace》的实质衔接是：SetSysWorkSpace 设置高阶 API 的系统区指针；Host 先用 GetLibApiWorkSpaceSize 计量，kernel 再经 GetSys/GetUserWorkspace 分区，RESERVED 故障验证偏移契约。
<!-- cannbot:related:end -->
