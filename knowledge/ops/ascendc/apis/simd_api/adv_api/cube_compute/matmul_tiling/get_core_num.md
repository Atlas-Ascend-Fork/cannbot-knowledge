---
type: API
title: GetCoreNum
description: 获得多核切分所使用的NumBlocks参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/GetCoreNum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetCoreNum

获得多核切分所使用的NumBlocks参数。

参数：
- dim（输出）：获取计算时所需要的核数， dim = mDim * nDim
- mDim（输出）：获取计算时M方向所需要的核数
- nDim（输出）：获取计算时N方向所需要的核数
- batchCoreM（输出）：获取计算时batch M方向所需要的核数，仅BatchMatmulTiling类支持
- batchCoreN（输出）：获取计算时batch N方向所需要的核数，仅BatchMatmulTiling类支持

返回值：-1表示获取失败； 0表示获取成功。

<!-- cannbot:related:start -->
## 相关

- [EnableMultiCoreSplitK](enable_multi_core_split_k.md)（`related`）：启用 SplitK 会改变实际参与核数和归并策略。
- [GetCoreNumAic](../../../../utils_api/platform_info/platform_ascend_c/get_core_num_aic.md)（`related`）：Matmul 使用 Cube 核数，应与平台 AIC 数量和 tiling 实际切分核数对照。
- [GetTiling](get_tiling.md)（`related`）：GetTiling 完成后才能读取最终 coreNum。
- [SetDim](set_dim.md)（`related`）：《SetDim》的任务是“设置多核Matmul参与运算的核数，区分纯Cube模式和MIX模式的分离与耦合场景”。《GetCoreNum》具体提供“获得多核切分所使用的NumBlocks参数。”，它直接用于Matmul 核数、单核形状、split range 与最终 TCubeTiling 的一致性。
- [SetSingleRange](set_single_range.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《GetCoreNum》明确“获得多核切分所使用的NumBlocks参数。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [GetSingleShape](get_single_shape.md)（`same_topic`）：GetSingleShape 与《GetCoreNum》的实质衔接是：GetSingleShape 返回 GetTiling 计算出的单核 M/N/K，必须与 SetSingleShape/Range、baseM/N/K、coreNum 和 TCubeTiling 字段保持一致。
- [Matmul Tiling类](matmul_tiling.md)（`same_topic`）：总页说明 GetCoreNum 是 tiling 求解结果而非简单平台核数。
<!-- cannbot:related:end -->
