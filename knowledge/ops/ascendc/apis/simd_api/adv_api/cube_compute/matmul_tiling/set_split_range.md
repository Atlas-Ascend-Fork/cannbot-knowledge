---
type: API
title: SetSplitRange
description: 设置baseM/baseN/baseK的最大值和最小值。目前Tiling暂时不支持该功能。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetSplitRange.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetSplitRange

设置baseM/baseN/baseK的最大值和最小值。目前Tiling暂时不支持该功能。

参数：
- maxBaseM（输入）：设置最大的baseM值，默认值为-1。-1表示不设置指定的baseM最大值，该值由Tiling函数自行计算。
- maxBaseN（输入）：设置最大的baseN值，默认值为-1。-1表示不设置指定的baseN最大值，该值由Tiling函数自行计算。
- maxBaseK（输入）：设置最大的baseK值，默认值为-1。-1表示不设置指定的baseK最大值，该值由Tiling函数自行计算。
- minBaseM（输入）：设置最小的baseM值，默认值为-1。-1表示不设置指定的baseM最小值，该值由Tiling函数自行计算。
- minBaseN（输入）：设置最小的baseN值，默认值为-1。-1表示不设置指定的baseN最小值，该值由Tiling函数自行计算。

返回值：-1表示设置失败；0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [Arange](../../../basic_api/reg_vector_compute/index_operations/arange.md)（`related`）：Arange 常用于构造索引，而 SetSplitRange 定义 Matmul 切分区间；仅在生成切分索引时衔接。
- [SetDim](set_dim.md)（`related`）：《SetDim》的任务是“设置多核Matmul参与运算的核数，区分纯Cube模式和MIX模式的分离与耦合场景”。《SetSplitRange》具体提供“设置baseM/baseN/baseK的最大值和最小值。目前Tiling暂时不支持该功能。”，它直接用于Matmul 核数、单核形状、split range 与最终 TCubeTiling 的一致性。
- [SetFixSplit](set_fix_split.md)（`related`）：《SetSplitRange》明确“设置baseM/baseN/baseK的最大值和最小值。目前Tiling暂时不支持该功能。”；它与《SetFixSplit》的“设置固定的baseM、baseN、baseK，单位为元素个数。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetSingleRange](set_single_range.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《SetSplitRange》明确“设置baseM/baseN/baseK的最大值和最小值。目前Tiling暂时不支持该功能。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
<!-- cannbot:related:end -->
