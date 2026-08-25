---
type: API
title: TPipe
description: 构造用来管理内存和同步的TPipe对象。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/TPipe_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# TPipe

头文件路径为："basic_api/kernel_tpipe.h"。

构造用来管理内存和同步的TPipe对象。

约束：-   避免TPipe在对象内创建和初始化，TPipe在对象内创建时，可能会影响编译器对对象内常量的优化，引起scalar性能劣化，具体原理
-   TPipe对象同一时刻全局只能存在一份，同时定义多个TPipe对象，会出现卡死等随机行为。如果需要使用多个TPipe时，请先调用Destroy接口释放前一个TPipe。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [DestroyWithoutPipeAll](destroy_without_pipe_all.md)（`related`）：《DestroyWithoutPipeAll》明确“释放TPipe资源，用于重复申请释放TPipe。内部未设置PIPE_ALL同步，需开发者自行保证同步流水正确。”；它与《TPipe》的“构造用来管理内存和同步的TPipe对象。”在实际调用参数、数据流或结果校验上直接衔接。
- [Init](init.md)（`related`）：TPipe 构造函数已经完成默认初始化；Init 卡说明额外 Init 的重置语义，二者共同防止构造后无条件再次初始化。
- [TPipe简介](t_pipe_intro.md)（`same_topic`）：《TPipe简介》明确“TPipe用于统一管理Device端内存等资源，一个Kernel函数必须且只能初始化一个TPipe对象。其主要功能包括：”；它与《TPipe》的“构造用来管理内存和同步的TPipe对象。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
