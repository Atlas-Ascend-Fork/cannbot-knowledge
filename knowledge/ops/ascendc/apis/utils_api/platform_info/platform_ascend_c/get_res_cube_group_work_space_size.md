---
type: API
title: GetResCubeGroupWorkSpaceSize
description: 基于CreateCubeResGroup进行AI Core分组计算需要传入workspace用于消息通信，在Host侧提供本接口用于获取CreateCubeResGroup所需要的workspace空间大小。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/GetResCubeGroupWorkSpaceSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# GetResCubeGroupWorkSpaceSize

## 功能说明
基于CreateCubeResGroup进行AI Core分组计算需要传入workspace用于消息通信，在Host侧提供本接口用于获取CreateCubeResGroup所需要的workspace空间大小。
## 函数原型
## 参数说明
无
## 返回值说明
当前CreateCubeResGroup所需要的workspace空间大小。
## 约束说明
无。

<!-- cannbot:related:start -->
## 相关

- [AllocMessage](../../../simd_api/basic_api/cube_group_mgmt/cube_res_group_handle/alloc_message.md)（`related`）：《AllocMessage》处理“AIV从消息队列里申请消息空间，用于存放消息结构体，返回当前申请的消息空间的地址。消息队列的深度固定为4，申请消息空间的顺序为自上而下，然后循环。当消息队列指针指向的消息空间为FREE状态时，AllocMessage返回空间的地址，否则循环等待，直到当前空间的状态为FREE。 图1 AllocMessage示意图”。《GetResCubeGroupWorkSpaceSize》明确“基于CreateCubeResGroup进行AI Core分组计算需要传入workspace用于消息通信，在Host侧提供本接口用于获取CreateCubeResGroup所需要的workspace空间大小。”，可直接用于核对AllocMessage/PostMessage/FreeMessage 生命周期、Cube 资源组句柄和 KFC workspace 合同。
- [CreateCubeResGroup](../../../simd_api/basic_api/cube_group_mgmt/cube_res_group_handle/create_cube_res_group.md)（`related`）：GetResCubeGroupWorkSpaceSize calculates the workspace that must be reserved before CreateCubeResGroup constructs the group.
- [CubeResGroupHandle](../../../simd_api/basic_api/cube_group_mgmt/cube_res_group_handle/cube_res_group_handle.md)（`related`）：CubeResGroupHandle 与《GetResCubeGroupWorkSpaceSize》的实质衔接是：CubeResGroupHandle 管理消息、队列、barrier 与 KFC workspace 生命周期，并约束 Cube 核执行。
<!-- cannbot:related:end -->
