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

- [逐 block 串行启动退化多核并行](../../../../runbooks/performance/block.md)（`exemplifies`）：串行 <<<1>>> 的修复要求一次启动 numBlocks，并在实现中用 GetCoreNumAiv 限制并行块数；该 API 提供可用 Vector 核数。
- [CalcTschNumBlocks](calc_tsch_num_blocks.md)（`related`）：CalcTschNumBlocks 计算 task scheduler block 数时需要 Vector 核资源信息；GetCoreNumAiv 提供分离架构下可用 AIV 数量。
- [GetCoreNumAic](get_core_num_aic.md)（`related`）：《GetCoreNumAiv》明确“获取当前硬件平台AI Core中Vector核数。若AI Core的架构为Cube、Vector分离模式，返回Vector Core的核数；耦合模式返回AI Core的核数。”；它与《GetCoreNumAic》的“获取当前硬件平台AI Core中Cube核数。若AI Core的架构为Cube、Vector分离模式，返回Cube Core的核数；耦合模式返回AI Core的核数。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
