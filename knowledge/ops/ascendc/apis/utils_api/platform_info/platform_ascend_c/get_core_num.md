---
type: API
title: GetCoreNum
description: 获取当前硬件平台的核数。若AI Core的架构为Cube、Vector分离模式，返回Vector Core的核数；耦合模式返回AI Core的核数。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/GetCoreNum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetCoreNum

## 功能说明
获取当前硬件平台的核数。若AI Core的架构为Cube、Vector分离模式，返回Vector Core的核数；耦合模式返回AI Core的核数。
## 函数原型
## 参数说明
无
## 返回值说明
Atlas 训练系列产品，耦合模式，返回AI Core的核数
Atlas 推理系列产品，耦合模式，返回AI Core的核数
Atlas A2 训练系列产品/Atlas A2 推理系列产品，分离模式，返回Vector Core的核数
Atlas A3 训练系列产品/Atlas A3 推理系列产品，分离模式，返回Vector Core的核数
Ascend 950PR/Ascend 950DT，分离模式，返回Vector Core的核数
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [GetCoreNumAic](get_core_num_aic.md)（`related`）：分离架构下 GetCoreNum 返回 Vector 核数；需要 Cube 分核时必须改用 GetCoreNumAic，避免 numBlocks 取错执行单元。
<!-- cannbot:related:end -->
