---
type: API
title: InitSpmBuffer
description: 初始化SPM Buffer。SPM Buffer是GM上的空间，当UB空间不足时可存放溢出数据。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/InitSpmBuffer.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# InitSpmBuffer

头文件路径为："basic_api/kernel_tpipe.h"。

初始化SPM Buffer。SPM Buffer是一块在GM上的空间，当UB空间不足时可以将溢出数据存放在SPM Buffer上。

参数：T: 待获取Tensor的数据类型，支持的类型请见LocalTensor相关描述。

约束：SPM Buffer供解决UB空间不足的特殊场景使用，性能较差，一般不推荐使用。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。
