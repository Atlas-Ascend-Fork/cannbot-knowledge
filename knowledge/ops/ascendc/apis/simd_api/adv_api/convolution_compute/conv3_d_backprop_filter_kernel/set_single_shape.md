---
type: API
title: SetSingleShape
description: 设置Conv3DBackpropFilter在单核上计算的形状。用于运行时修改shape。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Kernel/SetSingleShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetSingleShape

设置Conv3DBackpropFilter在单核上计算的形状。用于运行时修改shape。

函数原型：__aicore__ inline void SetSingleShape(uint64_t singleCoreM, uint64_t singleCoreN, uint64_t singleCoreK)

参数：
- singleCoreM（输入）：单核上M的大小，单位为元素个数。
- singleCoreN（输入）：单核上N的大小，单位为元素个数。
- singleCoreK（输入）：单核上K的大小，单位为元素个数。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。
