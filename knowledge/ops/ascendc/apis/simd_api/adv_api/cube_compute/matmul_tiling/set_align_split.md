---
type: API
title: SetAlignSplit
description: 多核切分时，设置singleCoreM/singleCoreN/singleCoreK的对齐值。比如设置singleCoreM的对齐值为64（单位为元素），切分出的singleCoreM为64的倍数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetAlignSplit.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetAlignSplit

多核切分时，设置singleCoreM/singleCoreN/singleCoreK的对齐值。比如设置singleCoreM的对齐值为64（单位为元素），切分出的singleCoreM为64的倍数。

参数：
- alignM（输入）：singleCoreM的对齐值。若传入-1或0，表示不设置指定的singleCoreM的对齐值，该值由Tiling函数自行计算。
- alignN（输入）：singleCoreN的对齐值。若传入-1或0，表示不设置指定的singleCoreN的对齐值，该值由Tiling函数自行计算。
- alignK（输入）：singleCoreK的对齐值。若传入-1或0，表示不设置指定的singleCoreK的对齐值，该值由Tiling函数自行计算。

返回值：-1表示设置失败； 0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [多核非对齐切分](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/multi_core_unaligned_split.md)（`explains`）：即使设置对齐值，矩阵总 M/N/K 不能整除 singleCore shape 时仍会出现尾块；指南要求在 Iterate 前用 SetTail 处理。
- [GetSingleShape](get_single_shape.md)（`related`）：SetAlignSplit 约束 singleCoreM/N/K 为指定倍数，GetSingleShape 可读回 Tiling 最终值并校验对齐约束是否真正生效。
- [SetALayout](set_a_layout.md)（`related`）：SetALayout 负责“设置A矩阵的Layout轴信息，包括B、S、N、G、D轴。对于BSNGD、SBNGD、BNGS1S2 Layout格式，调用IterateBatch接口之前，需要在Host侧Tiling实现中通过本接口设置A矩阵的Layout轴信息”；SetAlignSplit 负责“多核切分时，设置singleCoreM/singleCoreN/singleCoreK的对齐值。比如设置singleCoreM的对齐值为64（单位为元素），切分出的singleCoreM为64的倍数”。
- [SetSingleRange](set_single_range.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《SetAlignSplit》明确“多核切分时，设置singleCoreM/singleCoreN/singleCoreK的对齐值。比如设置singleCoreM的对齐值为64（单位为元素），切分出的singleCoreM为64的倍数。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
<!-- cannbot:related:end -->
