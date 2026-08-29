---
type: API
title: Reset
description: 完成自定义TBufPool资源的释放与eventId等变量的复位，调用后对应资源池及已分配Buffer不可继续使用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/custom_TBufPool/Reset.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# Reset

头文件路径为："basic_api/kernel_tpipe.h"。

完成自定义TbufPool资源的释放与eventId等变量的复位对消。

约束：切换自定义TBufPool资源池时调用该接口，调用后对应资源池及资源池分配的Buffer不能继续使用。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。
