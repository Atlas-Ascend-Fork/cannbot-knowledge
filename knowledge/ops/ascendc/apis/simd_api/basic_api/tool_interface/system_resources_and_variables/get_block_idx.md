---
type: API
title: GetBlockIdx
description: 获取当前逻辑AI Core的索引，用于多核逻辑控制及偏移量计算等。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetBlockIdx.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms: ['950', a2, a3]
---
# GetBlockIdx

头文件路径为："basic_api/kernel_operator_sys_var_intf.h"。

获取当前逻辑AI Core的索引，用于代码内部的多核逻辑控制及多核偏移量计算等。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。
