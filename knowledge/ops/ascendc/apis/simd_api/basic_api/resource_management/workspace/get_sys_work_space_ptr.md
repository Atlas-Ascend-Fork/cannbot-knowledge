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

- [507035 host tiling workspace 缺 RESERVED](../../../../../runbooks/compilation/register_none_tiling_reserved_workspace_507035.md)（`exemplifies`）：使用系统workspace时，host侧开发者需要自行申请系统workspace的空间，其预留空间大小可以通过GetLibApiWorkSpaceSize接口获取。`usrWorkspace = workspace + 16MB` 落在仅有 ~2MB 的 buffer 末尾之外 ~14MB，kernel 写 multiplier/addend 时 GM 越界 → 507035 向量核异常。接口卡的系统区申请合同直接解释该故障的越界地址；Host 总量计入平台 reserved 区即可同时覆盖系统指针和用户段。
- [GetLibApiWorkSpaceSize](../../../../utils_api/platform_info/platform_ascend_c/get_lib_api_work_space_size.md)（`related`）：获取AscendC API需要的workspace空间大小。；获取系统workspace指针。部分高阶API如Matmul需要使用系统workspace，相关接口需要传入系统workspace指针，此时可以通过该接口获取。使用系统workspace时，host侧开发者需要自行申请系统workspace的空间，其预留空间大小可以通过GetLibApiWorkSpaceSize接口获取。。GetLibApiWorkSpaceSize 给出 Host 侧预留容量，GetSysWorkSpacePtr 明确该容量由 Host 申请后在 Kernel 侧取得系统 workspace 指针，二者是同一 workspace 生命周期的容量端与地址端。
<!-- cannbot:related:end -->
