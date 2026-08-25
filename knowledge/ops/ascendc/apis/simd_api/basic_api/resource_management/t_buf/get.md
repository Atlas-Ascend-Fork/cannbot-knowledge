---
type: API
title: Get
description: 从TBuf上获取指定长度的Tensor，或者获取全部长度的Tensor。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TBuf/Get.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# Get

头文件路径为："basic_api/kernel_tpipe.h"。

从TBuf上获取指定长度的Tensor，或者获取全部长度的Tensor。

约束：len的数值是Tensor中元素的个数，len*sizeof(T)不能超过TBuf初始化时的长度。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。
