---
type: API
title: SetSingleRange
description: 设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetSingleRange.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetSingleRange

设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。

参数：
- maxM（输入）：设置最大的singleCoreM值，默认值为-1，表示不设置指定的singleCoreM最大值，该值由Tiling函数自行计算。
- maxN（输入）：设置最大的singleCoreN值，默认值为-1，表示不设置指定的singleCoreN最大值，该值由Tiling函数自行计算。
- maxK（输入）：设置最大的singleCoreK值，默认值为-1，表示不设置指定的singleCoreK最大值，该值由Tiling函数自行计算。
- minM（输入）：设置最小的singleCoreM值，默认值为-1，表示不设置指定的singleCoreM最小值，该值由Tiling函数自行计算。
- minN（输入）：设置最小的singleCoreN值，默认值为-1，表示不设置指定的singleCoreN最小值，该值由Tiling函数自行计算。

返回值：-1表示设置失败；0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [EnableMultiCoreSplitK](enable_multi_core_split_k.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《EnableMultiCoreSplitK》明确“多核场景，通过该接口开启切K轴。不调用该接口的情况下，默认不切K轴。在GetTiling接口调用前使用。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [GetBaseK](get_base_k.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《GetBaseK》明确“获取Tiling计算得到的baseK值。baseK参数的说明请参考表1。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [GetBaseM](get_base_m.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《GetBaseM》明确“获取Tiling计算得到的baseM值。baseM参数的说明请参考表1。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [GetBaseN](get_base_n.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《GetBaseN》明确“获取Tiling计算得到的baseN值。baseN参数的说明请参考表1。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [GetCoreNum](get_core_num.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《GetCoreNum》明确“获得多核切分所使用的NumBlocks参数。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [GetSingleShape](get_single_shape.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《GetSingleShape》明确“获取计算后的singleCoreM/singleCoreN/singleCoreK。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [GetTiling](get_tiling.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《GetTiling》明确“获取Tiling参数。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [Matmul Tiling类](matmul_tiling.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《Matmul Tiling类》明确“提供Matmul矩阵乘的Host侧Tiling类，包含TCubeTiling结构体、GetTiling及形状、类型、切分等参数设置方法。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [Matmul Tiling类使用说明](matmul_tiling_usage.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《Matmul Tiling类使用说明》明确“Ascend C提供一组Matmul Tiling API，方便用户获取Matmul kernel计算时所需的Tiling参数。用户只需要传入A/B/C矩阵的Position位置、Format格式和DType数据类型等信息，调用API接口，即可获取到Init中TCubeTiling结构体中的相关参数。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [SetAlignSplit](set_align_split.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《SetAlignSplit》明确“多核切分时，设置singleCoreM/singleCoreN/singleCoreK的对齐值。比如设置singleCoreM的对齐值为64（单位为元素），切分出的singleCoreM为64的倍数。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [SetFixSplit](set_fix_split.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《SetFixSplit》明确“设置固定的baseM、baseN、baseK，单位为元素个数。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [SetShape](set_shape.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《SetShape》明确“设置Matmul计算的形状m、n、k，可为完整矩阵或局部矩阵，支持传入-1按原始形状计算”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [SetSingleShape](set_single_shape.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《SetSingleShape》明确“设置Matmul单核计算的形状singleMIn，singleNIn，singleKIn，单位为元素。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [SetSplitRange](set_split_range.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《SetSplitRange》明确“设置baseM/baseN/baseK的最大值和最小值。目前Tiling暂时不支持该功能。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [TCubeTiling结构体](t_cube_tiling_struct.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《TCubeTiling结构体》明确“TCubeTiling结构体包含Matmul Tiling切分算法的相关参数，被传递给Matmul Kernel侧，用于Matmul的切块、搬运和计算过程等。TCubeTiling结构体的参数说明见表1。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
<!-- cannbot:related:end -->
