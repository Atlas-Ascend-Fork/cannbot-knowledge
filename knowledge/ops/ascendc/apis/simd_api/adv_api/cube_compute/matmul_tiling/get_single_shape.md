---
type: API
title: GetSingleShape
description: 获取计算后的singleCoreM/singleCoreN/singleCoreK。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/GetSingleShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetSingleShape

获取计算后的singleCoreM/singleCoreN/singleCoreK。

参数：
- shapeM（输出）：获取多核Tiling计算得到的singleCoreM值
- shapeN（输出）：获取多核Tiling计算得到的singleCoreN值
- shapeK（输出）：获取多核Tiling计算得到的singleCoreK值

返回值：-1表示设置失败； 0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [SetAlignSplit](set_align_split.md)（`related`）：SetAlignSplit 约束 singleCoreM/N/K 为指定倍数，GetSingleShape 可读回 Tiling 最终值并校验对齐约束是否真正生效。
- [SetDim](set_dim.md)（`related`）：《SetDim》的任务是“设置多核Matmul参与运算的核数，区分纯Cube模式和MIX模式的分离与耦合场景”。《GetSingleShape》具体提供“获取计算后的singleCoreM/singleCoreN/singleCoreK。”，它直接用于Matmul 核数、单核形状、split range 与最终 TCubeTiling 的一致性。
- [SetSingleOutputShape](../../convolution_compute/conv3_d_kernel/set_single_output_shape.md)（`related`）：SetSingleOutputShape 与《GetSingleShape》的实质衔接是：SetSingleOutputShape 定义单核 Co/Do/M 输出分块；Conv3D kernel、tiling、shape 查询与 Iterate 的参数必须按同一 M 合轴输出契约传递。
- [SetSingleRange](set_single_range.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《GetSingleShape》明确“获取计算后的singleCoreM/singleCoreN/singleCoreK。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [GetBaseK](get_base_k.md)（`same_topic`）：GetSingleShape 与《GetBaseK》的实质衔接是：GetSingleShape 返回 GetTiling 计算出的单核 M/N/K，必须与 SetSingleShape/Range、baseM/N/K、coreNum 和 TCubeTiling 字段保持一致。
- [GetBaseM](get_base_m.md)（`same_topic`）：GetBaseM 与《GetSingleShape》的实质衔接是：baseM 与 baseN/baseK 一起写入 TCubeTiling，由输入 shape、single shape 与 GetTiling 计算；Matmul 使用说明解释该块大小如何驱动 kernel 循环。
- [GetBaseN](get_base_n.md)（`same_topic`）：GetSingleShape 与《GetBaseN》的实质衔接是：GetSingleShape 返回 GetTiling 计算出的单核 M/N/K，必须与 SetSingleShape/Range、baseM/N/K、coreNum 和 TCubeTiling 字段保持一致。
- [GetCoreNum](get_core_num.md)（`same_topic`）：GetSingleShape 与《GetCoreNum》的实质衔接是：GetSingleShape 返回 GetTiling 计算出的单核 M/N/K，必须与 SetSingleShape/Range、baseM/N/K、coreNum 和 TCubeTiling 字段保持一致。
- [GetTiling](get_tiling.md)（`same_topic`）：GetSingleShape 与《GetTiling》的实质衔接是：GetSingleShape 返回 GetTiling 计算出的单核 M/N/K，必须与 SetSingleShape/Range、baseM/N/K、coreNum 和 TCubeTiling 字段保持一致。
- [Matmul Tiling类](matmul_tiling.md)（`same_topic`）：GetSingleShape 与《Matmul Tiling类》的实质衔接是：GetSingleShape 返回 GetTiling 计算出的单核 M/N/K，必须与 SetSingleShape/Range、baseM/N/K、coreNum 和 TCubeTiling 字段保持一致。
- [Matmul Tiling类使用说明](matmul_tiling_usage.md)（`same_topic`）：GetSingleShape 与《Matmul Tiling类使用说明》的实质衔接是：GetSingleShape 返回 GetTiling 计算出的单核 M/N/K，必须与 SetSingleShape/Range、baseM/N/K、coreNum 和 TCubeTiling 字段保持一致。
- [SetSingleShape](../../convolution_compute/conv3_d_backprop_filter_kernel/set_single_shape.md)（`same_topic`）：GetSingleShape 与《SetSingleShape》的实质衔接是：GetSingleShape 返回 GetTiling 计算出的单核 M/N/K，必须与 SetSingleShape/Range、baseM/N/K、coreNum 和 TCubeTiling 字段保持一致。
- [SetSingleShape](../../convolution_compute/conv3_d_backprop_input_kernel/set_single_shape.md)（`same_topic`）：GetSingleShape 与《SetSingleShape》的实质衔接是：GetSingleShape 返回 GetTiling 计算出的单核 M/N/K，必须与 SetSingleShape/Range、baseM/N/K、coreNum 和 TCubeTiling 字段保持一致。
- [SetSingleShape](../matmul_kernel/set_single_shape.md)（`same_topic`）：GetSingleShape 与《SetSingleShape》的实质衔接是：GetSingleShape 返回 GetTiling 计算出的单核 M/N/K，必须与 SetSingleShape/Range、baseM/N/K、coreNum 和 TCubeTiling 字段保持一致。
- [SetSingleShape](set_single_shape.md)（`same_topic`）：GetSingleShape 与《SetSingleShape》的实质衔接是：GetSingleShape 返回 GetTiling 计算出的单核 M/N/K，必须与 SetSingleShape/Range、baseM/N/K、coreNum 和 TCubeTiling 字段保持一致。
- [TCubeTiling结构体](t_cube_tiling_struct.md)（`same_topic`）：GetSingleShape 与《TCubeTiling结构体》的实质衔接是：GetSingleShape 返回 GetTiling 计算出的单核 M/N/K，必须与 SetSingleShape/Range、baseM/N/K、coreNum 和 TCubeTiling 字段保持一致。
<!-- cannbot:related:end -->
