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
