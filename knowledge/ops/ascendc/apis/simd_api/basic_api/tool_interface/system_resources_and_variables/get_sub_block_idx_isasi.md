---
type: API
title: GetSubBlockIdx
description: 在分离模式架构下，获取逻辑AI Core上AIC或AIV的逻辑索引。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetSubBlockIdx_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# GetSubBlockIdx

头文件路径为： "basic_api/kernel_operator_sys_var_intf.h"。

在分离模式架构下，获取逻辑AI Core上Cube Core（AIC）或者Vector Core（AIV）的逻辑索引。

GetSubBlockIdx在使用__mix__(1, 2)作为函数执行空间限定符的场景下，可以用于区分同一个核上的两个不同Vector Core，取值分别为0和1。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Kirin X90、Kirin 9030 支持。
