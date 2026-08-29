---
type: API
title: Reset
description: 切换TBufPool资源池时使用，结束当前资源池相关事件，资源池及Buffer仍然存在。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TBufPool/Reset.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# Reset

头文件路径为："basic_api/kernel_tpipe.h"。

在切换TBufPool资源池时使用，结束当前TbufPool资源池正在处理的相关事件。调用后当前资源池及资源池分配的Buffer仍然存在，只是Buffer内容可能会被改写。可以切换回该资源池后，重新开始使用该Buffer，无需再次分配。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。
