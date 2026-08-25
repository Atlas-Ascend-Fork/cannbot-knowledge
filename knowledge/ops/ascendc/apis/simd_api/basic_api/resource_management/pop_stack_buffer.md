---
type: API
title: PopStackBuffer
description: 在指定position（逻辑位置）申请临时空间，空间大小为指定position的全部剩余空间。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/PopStackBuffer.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# PopStackBuffer

在指定position（逻辑位置）申请临时空间，空间大小为指定position的全部剩余空间。

约束：-   该接口不支持嵌套使用，比如函数A中调用了PopStackBuffer，那么调用函数A的其他函数中则不可以再调用PopStackBuffer。
-   因为当前高阶API内部实现中会使用到本接口，所以算子实现中调用了高阶API的场景，不支持调用该接口。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。
