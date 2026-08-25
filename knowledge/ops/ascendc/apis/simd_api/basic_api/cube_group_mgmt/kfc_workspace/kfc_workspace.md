---
type: API
title: KfcWorkspace
description: KfcWorkspace 接口集，用于管理 Kfc 工作区内存，含构造与析构函数、UpdateKfcWorkspace、GetKfcWorkspace 等。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/KfcWorkspace/KfcWorkspace.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2]
---

# KfcWorkspace

KfcWorkspace 接口集，用于管理 Kfc 工作区内存，含构造与析构函数、UpdateKfcWorkspace、GetKfcWorkspace 等。

用于创建KfcWorkspace对象，Kfc全称为kernel function call，表示核间通信调用。

本接口组包含 构造函数与析构函数, UpdateKfcWorkspace，辅助接口包括 GetKfcWorkspace。

返回值：KfcWorkspace对象实例。

约束：不能和REGIST_MATMUL_OBJ接口同时使用。使用资源管理API时，用户自主管理AIC和AIV的核间通信，REGIST_MATMUL_OBJ内部是由框架管理AIC和AIV的核间通信，同时使用可能会导致通信消息错误等异常。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
