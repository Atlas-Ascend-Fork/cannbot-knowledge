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

<!-- cannbot:related:start -->
## 相关

- [GetKfcWorkspace](get_kfc_workspace.md)（`same_topic`）：GetKfcWorkspace 与《KfcWorkspace》的实质衔接是：GetKfcWorkspace 返回 CubeResGroup 消息区 GM 地址；KfcWorkspace 构造/Get/Update 和资源组 handle 共同管理该地址的生命周期。
- [UpdateKfcWorkspace](update_kfc_workspace.md)（`same_topic`）：UpdateKfcWorkspace 与《KfcWorkspace》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
- [构造函数与析构函数](constructor_and_destructor.md)（`same_topic`）：构造函数与析构函数 与《KfcWorkspace》的实质衔接是：KfcWorkspace 构造把 GM 区域交给 CubeResGroup 消息通信，Get/Update workspace 与创建资源组/handle 共同管理该地址生命周期。
<!-- cannbot:related:end -->
