---
type: API
title: CubeResGroupHandle
description: CubeResGroupHandle 接口集，提供 Cube 资源分组管理能力，含构造函数、CreateCubeResGroup、AssignQueue、PostMessage 等。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/CubeResGroupHandle/CubeResGroupHandle.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2]
---

# CubeResGroupHandle

Cube 资源分组管理句柄，用于在 ISASI Cube 计算中对资源进行分组与消息调度。通过 CreateCubeResGroup 创建分组，配合 AssignQueue、AllocMessage、PostMessage、PostFakeMsg、Wait、FreeMessage 实现消息的分配、发送、等待与释放；SetQuit、SetSkipMsg 用于退出与跳过控制。适用于多任务并发调度场景，需先完成使用说明中要求的初始化流程。
