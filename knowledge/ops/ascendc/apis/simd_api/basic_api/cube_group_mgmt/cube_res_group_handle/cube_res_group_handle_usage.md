---
type: API
title: CubeResGroupHandle
description: 在分离模式下对AI Core计算资源分组，通过Client和Server架构实现AIV与AIC间的消息通信和任务分发。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/CubeResGroupHandle/CubeResGroupHandle_usage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2]
---

# CubeResGroupHandle

在分离模式下对 AI Core 计算资源分组，通过 Client-Server 架构实现 AIV（Vector Core）与 AIC（Cube Core）间的消息通信和任务分发。

使用流程：CreateCubeResGroup 创建资源组 → AIV 调用 AllocMessage 申请消息空间 → 构造 CubeMsgType 消息并 PostMessage 发送 → AIC 通过回调函数处理消息 → FreeMessage 释放 → AIV 调用 Wait 等待处理完成。消息队列深度固定为 4，消息状态含 FREE、IDLE、PROCESSING、DONE 等。支持 PostFakeMsg/SetSkipMsg 实现消息合并，SetQuit 发送退出消息。CubeMsgType 由用户定义，包含 tilingData、msgState、msgOffset 等字段。支持 950/a2。
