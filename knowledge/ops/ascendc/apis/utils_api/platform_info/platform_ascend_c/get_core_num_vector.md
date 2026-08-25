---
type: API
title: GetCoreNumVector
description: 用于获取硬件平台独立的Vector Core的核数。 该接口仅在Atlas 推理系列产品有效，其他硬件平台型号均返回0。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/GetCoreNumVector.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetCoreNumVector

## 功能说明
用于获取硬件平台独立的Vector Core的核数。
该接口仅在Atlas 推理系列产品有效，其他硬件平台型号均返回0。
## 函数原型
## 参数说明
无
## 返回值说明
返回硬件平台Vector Core的核数。
## 约束说明
Atlas 训练系列产品，不支持该接口，返回0
Atlas 推理系列产品，支持该接口，返回硬件平台Vector Core的核数
Atlas A2 训练系列产品/Atlas A2 推理系列产品不支持该接口，返回0
Atlas A3 训练系列产品/Atlas A3 推理系列产品不支持该接口，返回0
Atlas 200I/500 A2 推理产品不支持该接口，返回0
Ascend 950PR/Ascend 950DT不支持该接口，返回0

<!-- cannbot:related:start -->
## 相关

- [block 数应覆盖可用 Vector 核](../../../../runbooks/performance/block_count_uses_all_available_vector_cores.md)（`exemplifies`）：Runbook 要求使用目标设备实测 Vector 核数，而该 API 明确在 A3 返回 0、只对独立 Vector Core 的特定推理产品有效，构成防止选错探针的关键边界。
- [EnableVectorCore](../../../../guides/programming_guide/appendix/common_operations/enable_vector_core.md)（`explains`）：EnableVectorCore 明确要求 Host 把 numBlocks 设为 AI Core 与 Vector Core 总数，GetCoreNumVector 提供 Vector 部分的计数。
- [设置Kernel类型](../../../simd_api/basic_api/kernel_tiling/set_kernel_type.md)（`related`）：设置Kernel类型：SetKernelType的目标是只启动需要的 AIC/AIV核；优化指南解释选型，kernel_type runbook证明裸字段赋值无效，GetCoreNumAic/Vector提供合法核数输入。 目标卡《GetCoreNumVector》补充：用于获取硬件平台独立的Vector Core的核数。 该接口仅在Atlas 推理系列产品有效，其他硬件平台型号均返回0。
- [GetCoreNumAic](get_core_num_aic.md)（`same_topic`）：《GetCoreNumVector》明确“用于获取硬件平台独立的Vector Core的核数。 该接口仅在Atlas 推理系列产品有效，其他硬件平台型号均返回0。”；它与《GetCoreNumAic》的“获取当前硬件平台AI Core中Cube核数。若AI Core的架构为Cube、Vector分离模式，返回Cube Core的核数；耦合模式返回AI Core的核数。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
