---
type: API
title: 卷积计算End
description: 在Conv3DBackpropFilter卷积反向计算完成后，必须调用一次End，以清除EventID并释放内部申请的临时内存。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Kernel/End.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# 卷积计算End

在Conv3DBackpropFilter卷积反向计算完成后，必须调用一次End，以清除EventID并释放内部申请的临时内存。

函数原型：__aicore__ inline void End()

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。
