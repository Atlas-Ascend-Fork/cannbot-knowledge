---
type: API
title: CubeResGroupHandle构造函数
description: 构造CubeResGroupHandle对象，完成组内的AIC和消息队列分配。构造CubeResGroupHandle对象时需要传入模板参数CubeMsgType，CubeMsgType是由用户定义的消息结构体，请参考表1。使用此接口需要用户自主管理地址、同步事件等，因此更推荐使用CreateCubeResGroup接口快速创建CubeResGroupHandle对象。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/CubeResGroupHandle/CubeResGroupHandle_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2]
---

# CubeResGroupHandle构造函数

构造 CubeResGroupHandle 对象，完成组内 AIC 和消息队列分配。需传入模板参数 CubeMsgType（用户定义的消息结构体）。使用此接口需用户自主管理地址、同步事件等，推荐使用 CreateCubeResGroup 替代。

原型：`CubeResGroupHandle(GM_ADDR workspace, uint8_t blockStart, uint8_t blockSize, uint8_t msgQueueSize, uint8_t evtIDIn)`。参数：workspace（GM 工作空间地址）、blockStart、blockSize、msgQueueSize、evtIDIn（同步事件 ID）。支持 950/a2。

<!-- cannbot:related:start -->
## 相关

- [AllocMessage](alloc_message.md)（`related`）：《AllocMessage》处理“AIV从消息队列里申请消息空间，用于存放消息结构体，返回当前申请的消息空间的地址。消息队列的深度固定为4，申请消息空间的顺序为自上而下，然后循环。当消息队列指针指向的消息空间为FREE状态时，AllocMessage返回空间的地址，否则循环等待，直到当前空间的状态为FREE。 图1 AllocMessage示意图”。《CubeResGroupHandle构造函数》明确“构造CubeResGroupHandle对象，完成组内的AIC和消息队列分配。构造CubeResGroupHandle对象时需要传入模板参数CubeMsgType，CubeMsgType是由用户定义的消息结构体，请参考表1。使用此接口需要用户自主管理地址、同步事件等，因此更推荐使用CreateCubeResGroup接口快速创建CubeResGroupHandle对象。”，可直接用于核对AllocMessage/PostMessage/FreeMessage 生命周期、Cube 资源组句柄和 KFC workspace 合同。
- [CreateCubeResGroup](create_cube_res_group.md)（`related`）：构造函数正文建议通过 CreateCubeResGroup 统一创建 Handle，以完成队列和事件资源分配并避免直接构造冲突。
- [GetKfcWorkspace](../kfc_workspace/get_kfc_workspace.md)（`same_topic`）：GetKfcWorkspace 与《CubeResGroupHandle构造函数》的实质衔接是：GetKfcWorkspace 返回 CubeResGroup 消息区 GM 地址；KfcWorkspace 构造/Get/Update 和资源组 handle 共同管理该地址的生命周期。
- [UpdateKfcWorkspace](../kfc_workspace/update_kfc_workspace.md)（`same_topic`）：UpdateKfcWorkspace 与《CubeResGroupHandle构造函数》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
<!-- cannbot:related:end -->
