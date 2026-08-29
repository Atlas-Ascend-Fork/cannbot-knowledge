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

<!-- cannbot:related:start -->
## 相关

- [双AIV CrossCoreFlag 的 subBlock 契约缺陷](../../../../../runbooks/compilation/aiv_crosscoreflag_subblock_507015.md)（`exemplifies`）：焦点卡的修法要求“按 `GetSubBlockIdx() * FLAG_ID_MAX` 偏移区分 V0/V1”，候选卡说明 GetSubBlockIdx 可“区分同一个核上的两个不同Vector Core，取值分别为0和1”；该返回值正是选择两段 flag 池的索引。
- [GetTaskRatio](get_task_ratio.md)（`related`）：GetSubBlockIdx在使用__mix__(1, 2)作为函数执行空间限定符的场景下，可以用于区分同一个核上的两个不同Vector Core，取值分别为0和1。；分离模式下，获取任务启动的Cube Core（AIC）或者Vector Core（AIV）的数量与逻辑AI Core数量的比例。。GetTaskRatio 给出 MIX 分离任务中 AIC/AIV 数量比例，GetSubBlockIdx 再区分同一逻辑核内的两个 Vector Core，联合可解释分核与子核身份。
<!-- cannbot:related:end -->
