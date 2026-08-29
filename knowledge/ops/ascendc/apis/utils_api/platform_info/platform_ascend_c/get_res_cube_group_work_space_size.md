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

- [CreateCubeResGroup](../../../simd_api/basic_api/cube_group_mgmt/cube_res_group_handle/create_cube_res_group.md)（`related`）：快速创建 CubeResGroupHandle 对象，内部完成消息队列空间和同步事件分配。；基于CreateCubeResGroup进行AI Core分组计算需要传入workspace用于消息通信，在Host侧提供本接口用于获取CreateCubeResGroup所需要的workspace空间大小。；创建接口分配队列与同步资源，而 Host 查询接口给出该分组通信所需 workspace 的字节容量，调用方必须先按查询值分配再创建资源组。
<!-- cannbot:related:end -->
