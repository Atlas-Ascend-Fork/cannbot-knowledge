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

- [EnableVectorCore](../../../../guides/programming_guide/appendix/common_operations/enable_vector_core.md)（`explains`）：启用 Vector Core 时 numBlocks 需超过 AI Core 数并通常取 AIC+AIV，GetCoreNumAic 提供判定阈值和总数中的 AIC 部分。
- [CalcTschNumBlocks](calc_tsch_num_blocks.md)（`related`）：CalcTschNumBlocks 还需结合 Cube 核数判断 AIC:AIV 拓扑比例；GetCoreNumAic 提供该资源侧输入。
- [GetCoreNum](../../../simd_api/adv_api/cube_compute/matmul_tiling/get_core_num.md)（`related`）：Matmul 使用 Cube 核数，应与平台 AIC 数量和 tiling 实际切分核数对照。
- [GetCoreNum](get_core_num.md)（`related`）：分离架构下 GetCoreNum 返回 Vector 核数；需要 Cube 分核时必须改用 GetCoreNumAic，避免 numBlocks 取错执行单元。
- [GetCoreNumAiv](get_core_num_aiv.md)（`related`）：《GetCoreNumAiv》明确“获取当前硬件平台AI Core中Vector核数。若AI Core的架构为Cube、Vector分离模式，返回Vector Core的核数；耦合模式返回AI Core的核数。”；它与《GetCoreNumAic》的“获取当前硬件平台AI Core中Cube核数。若AI Core的架构为Cube、Vector分离模式，返回Cube Core的核数；耦合模式返回AI Core的核数。”在实际调用参数、数据流或结果校验上直接衔接。
- [设置Kernel类型](../../../simd_api/basic_api/kernel_tiling/set_kernel_type.md)（`related`）：设置Kernel类型：SetKernelType的目标是只启动需要的 AIC/AIV核；优化指南解释选型，kernel_type runbook证明裸字段赋值无效，GetCoreNumAic/Vector提供合法核数输入。 目标卡《GetCoreNumAic》补充：获取当前硬件平台AI Core中Cube核数。若AI Core的架构为Cube、Vector分离模式，返回Cube Core的核数；耦合模式返回AI Core的核数。
- [GetCoreNumVector](get_core_num_vector.md)（`same_topic`）：《GetCoreNumVector》明确“用于获取硬件平台独立的Vector Core的核数。 该接口仅在Atlas 推理系列产品有效，其他硬件平台型号均返回0。”；它与《GetCoreNumAic》的“获取当前硬件平台AI Core中Cube核数。若AI Core的架构为Cube、Vector分离模式，返回Cube Core的核数；耦合模式返回AI Core的核数。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
