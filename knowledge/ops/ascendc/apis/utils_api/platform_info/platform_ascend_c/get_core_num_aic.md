---
type: API
title: GetCoreNumAic
description: 获取当前硬件平台AI Core中Cube核数。若AI Core的架构为Cube、Vector分离模式，返回Cube Core的核数；耦合模式返回AI
  Core的核数。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/GetCoreNumAic.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetCoreNumAic

## 功能说明
获取当前硬件平台AI Core中Cube核数。若AI Core的架构为Cube、Vector分离模式，返回Cube Core的核数；耦合模式返回AI Core的核数。
## 函数原型
## 参数说明
无
## 返回值说明
Atlas 训练系列产品，耦合模式，返回AI Core的核数
Atlas 推理系列产品，耦合模式，返回AI Core的核数
Atlas A2 训练系列产品/Atlas A2 推理系列产品，分离模式，返回Cube Core的核数
Atlas A3 训练系列产品/Atlas A3 推理系列产品，分离模式，返回Cube Core的核数
Ascend 950PR/Ascend 950DT，分离模式，返回Cube Core的核数
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [GetCoreNum](get_core_num.md)（`related`）：获取当前硬件平台的核数。若AI Core的架构为Cube、Vector分离模式，返回Vector Core的核数；耦合模式返回AI Core的核数。；获取当前硬件平台AI Core中Cube核数。若AI Core的架构为Cube、Vector分离模式，返回Cube Core的核数；耦合模式返回AI Core的核数。。两卡共同处理耦合与 Cube/Vector 分离架构下的核数查询，但通用 GetCoreNum 在分离模式返回 Vector 数，GetCoreNumAic 返回 Cube 数，联合阅读可避免按错执行单元分核。
<!-- cannbot:related:end -->
