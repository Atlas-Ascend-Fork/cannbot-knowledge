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

- [核函数内删除Workspace相关冗余操作](../../../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/remove_workspace_redundancy.md)（`explains`）：“在Ascend C算子工程中，编写核函数时传入的参数workspace已经直接赋值为用户Workspace，因此无需再通过SetSysWorkspace和GetUserWorkspace来设置和获取Workspace。”与“框架需要使用的workspace称之为系统workspace。Matmul Kernel侧接口等高阶API需要系统workspace，所以在使用该类API时，需要调用该接口，设置系统workspace的指针。”分别给出双端正文事实；优化指南区分用户 workspace 的冗余设置与高阶 API 需要的系统 workspace，SetSysWorkSpace 卡给出后一类调用条件，二者形成删除冗余而保留必要设置的决策边界。
- [All 950 ACLNN 算子知识](../../../../../operators/aclnn/math/math/all_950.md)（`related`）：entry 先 `SetSysWorkspace(workspace)`，再以 `GetUserWorkspace(workspace)` 取得用户区；任一指针为空立即返回。分组第一阶段把每个 group/core 的部分结果写用户区，第二阶段在 `SyncAll()` 后从该区归约到输出。单阶段路线不消费用户区，但固定 16 MiB 系统 reserve 仍由 Tiling 上报。Cast、Fill 和 ViewCopy 的 workspace 也由 executor 汇总，故 ACLNN `workspaceSize` 不能用上式单独替代。；框架需要使用的workspace称之为系统workspace。Matmul Kernel侧接口等高阶API需要系统workspace，所以在使用该类API时，需要调用该接口，设置系统workspace的指针。采用工程化算子开发方式或者kernel直调方式（开启HAVE_WORKSPACE编译选项）时，不需要开发者手动设置，框架会自动设置。其他场景下，需要开发者调用SetSysWorkSpace进行设置。；算子 entry 的第一步调用与目标 API 的系统 workspace 设置合同完全对应，且直接影响分组路线能否继续。
- [Expand 950 ACLNN 算子知识](../../../../../operators/aclnn/math/math/expand_950.md)（`related`）：entry 先 `SetSysWorkspace`；Matmul Kernel侧接口等高阶API需要系统workspace，所以在使用该类API时，需要调用该接口，设置系统workspace的指针；Expand 950 的 Kernel entry 实际调用与资源管理 API 的系统工作区合同直接衔接。
- [FastGelu 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/fast_gelu_950.md)（`related`）：“entry 先检查 workspace，调用 `SetSysWorkspace`，再取得 `GetUserWorkspace(workspace)`；”给出 FastGelu 的实际 entry 顺序；“在kernel侧调用该接口前，需要在host侧调用GetLibApiWorkSpaceSize获取系统workspace的大小，并在host侧设置workspacesize大小。”补齐 Host 侧系统 workspace 前置。
- [GatherNd 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/index/gather_nd_950.md)（`related`）：Tiling 读取平台 AIV 核数和 UB，先保留 32 KiB DCache；所有 Route 的 `GetWorkspaceSize` 都令 GatherNd 节点 workspace 为 `16,777,216` 字节。entry 要求框架 workspace、`GetUserWorkspace` 均非空，调用 `SetSysWorkspace`，但五个可达 body 没有对 user workspace 的 load/store。Matmul Kernel侧接口等高阶API需要系统workspace，所以在使用该类API时，需要调用该接口，设置系统workspace的指针。算子卡给出 entry 的实际系统 workspace 设置和 16 MiB 申报，接口卡定义系统指针的职责；这能区分框架系统区设置与五个 body 未消费的用户区，避免误删 entry 调用或误判 user workspace 数据流。
- [GetUserWorkspace](get_user_workspace.md)（`related`）：获取用户使用的workspace指针。Kernel直调开发方式下，如果未开启HAVE_WORKSPACE编译选项，框架不会自动设置系统workspace。如果使用了Matmul Kernel侧接口等需要系统workspace的高阶API，kernel侧需要通过SetSysWorkSpace设置系统workspace，此时用户workspace需要通过该接口获取。；框架需要使用的workspace称之为系统workspace。Matmul Kernel侧接口等高阶API需要系统workspace，所以在使用该类API时，需要调用该接口，设置系统workspace的指针。；GetUserWorkspace 明确在高阶 API 需要系统 workspace 时配合 SetSysWorkSpace 使用，两者划分并连接用户区与系统区。
<!-- cannbot:related:end -->
