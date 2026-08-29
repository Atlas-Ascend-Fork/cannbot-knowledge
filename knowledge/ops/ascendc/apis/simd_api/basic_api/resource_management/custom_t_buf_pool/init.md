---
type: API
title: Init
description: 完成自定义TBufPool资源与eventId等变量的初始化操作，可在自定义构造函数中调用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/custom_TBufPool/Init.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# Init

头文件路径为："basic_api/kernel_tpipe.h"。

完成自定义TbufPool资源与eventId等变量的初始化操作。

约束：用户可在自定义的构造函数中调用该接口，也可自行实现。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。
