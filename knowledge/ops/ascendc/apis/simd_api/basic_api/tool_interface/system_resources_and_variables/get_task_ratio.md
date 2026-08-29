---
type: API
title: GetTaskRatio
description: 分离模式下获取AIC或AIV数量与逻辑AI Core数量的比例，耦合模式固定返回1。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetTaskRatio.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# GetTaskRatio

头文件路径为："basic_api/kernel_operator_sys_var_intf.h"。

分离模式下，获取任务启动的Cube Core（AIC）或者Vector Core（AIV）的数量与逻辑AI Core数量的比例。

- 在AIC上调用时返回AIC数量与逻辑AI Core数量的比例。
- 在AIV上调用时返回AIV数量与逻辑AI Core数量的比例。

耦合模式下，固定返回1。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [GetSubBlockIdx](get_sub_block_idx_isasi.md)（`related`）：GetSubBlockIdx在使用__mix__(1, 2)作为函数执行空间限定符的场景下，可以用于区分同一个核上的两个不同Vector Core，取值分别为0和1。；分离模式下，获取任务启动的Cube Core（AIC）或者Vector Core（AIV）的数量与逻辑AI Core数量的比例。。GetTaskRatio 给出 MIX 分离任务中 AIC/AIV 数量比例，GetSubBlockIdx 再区分同一逻辑核内的两个 Vector Core，联合可解释分核与子核身份。
<!-- cannbot:related:end -->
