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

- [507035 host tiling workspace 缺 RESERVED](../../../../../runbooks/compilation/register_none_tiling_reserved_workspace_507035.md)（`exemplifies`）：“host `GetWorkspaceSize` → `workspaces［0］` → 框架生成的 kernel wrapper → `SetSysWorkspaceForce(workspace)` + `usrWorkspace = workspace + AscendC::RESERVED_WORKSPACE` → kernel `workspace` 形参。”展示 wrapper 将用户段偏移 RESERVED_WORKSPACE 后才传入 kernel；“获取用户使用的workspace指针。Kernel直调开发方式下，如果未开启HAVE_WORKSPACE编译选项，框架不会自动设置系统workspace。如果使用了Matmul Kernel侧接口等需要系统workspace的高阶API，kernel侧需要通过SetSysWorkSpace设置系统workspace，此时用户workspace需要通过该接口获取。”定义系统区与用户区共存时应获取用户 workspace。该实例用于验证 Host 总大小必须包含保留区与用户写入量。
- [SetSysWorkSpace](set_sys_work_space.md)（`related`）：获取用户使用的workspace指针。Kernel直调开发方式下，如果未开启HAVE_WORKSPACE编译选项，框架不会自动设置系统workspace。如果使用了Matmul Kernel侧接口等需要系统workspace的高阶API，kernel侧需要通过SetSysWorkSpace设置系统workspace，此时用户workspace需要通过该接口获取。；框架需要使用的workspace称之为系统workspace。Matmul Kernel侧接口等高阶API需要系统workspace，所以在使用该类API时，需要调用该接口，设置系统workspace的指针。；GetUserWorkspace 明确在高阶 API 需要系统 workspace 时配合 SetSysWorkSpace 使用，两者划分并连接用户区与系统区。
<!-- cannbot:related:end -->
