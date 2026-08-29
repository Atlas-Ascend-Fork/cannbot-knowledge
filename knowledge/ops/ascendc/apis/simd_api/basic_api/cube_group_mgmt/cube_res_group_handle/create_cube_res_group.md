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

- [GetResCubeGroupWorkSpaceSize](../../../../utils_api/platform_info/platform_ascend_c/get_res_cube_group_work_space_size.md)（`related`）：快速创建 CubeResGroupHandle 对象，内部完成消息队列空间和同步事件分配。；基于CreateCubeResGroup进行AI Core分组计算需要传入workspace用于消息通信，在Host侧提供本接口用于获取CreateCubeResGroup所需要的workspace空间大小。；创建接口分配队列与同步资源，而 Host 查询接口给出该分组通信所需 workspace 的字节容量，调用方必须先按查询值分配再创建资源组。
<!-- cannbot:related:end -->
