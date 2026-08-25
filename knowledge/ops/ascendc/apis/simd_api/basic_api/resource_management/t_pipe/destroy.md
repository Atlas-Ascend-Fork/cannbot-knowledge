---
type: API
title: Destroy
description: 释放TPipe资源，用于重复申请释放TPipe，创建TPipe对象后可调用Destroy手动释放资源。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/Destroy.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# Destroy

头文件路径为："basic_api/kernel_tpipe.h"。

释放资源。

约束：用于重复申请释放tpipe，创建tpipe对象后，可调用Destroy手动释放资源。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。
