---
type: API
title: GetCoreNumAiv
description: 获取当前硬件平台AI Core中Vector核数。若AI Core的架构为Cube、Vector分离模式，返回Vector Core的核数；耦合模式返回AI
  Core的核数。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/GetCoreNumAiv.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetCoreNumAiv

## 功能说明
获取当前硬件平台AI Core中Vector核数。若AI Core的架构为Cube、Vector分离模式，返回Vector Core的核数；耦合模式返回AI Core的核数。
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

- [GetCoreNum](get_core_num.md)（`same_topic`）：获取当前硬件平台的核数。；获取当前硬件平台AI Core中Vector核数。。两卡的产品表给出同一返回合同：分离架构返回 Vector Core 数、耦合架构返回 AI Core 数；它们是围绕同一平台核数查询决策的两个入口说明。
<!-- cannbot:related:end -->
