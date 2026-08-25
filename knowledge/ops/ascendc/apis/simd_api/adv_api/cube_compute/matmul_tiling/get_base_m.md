---
type: API
title: GetBaseM
description: 获取Tiling计算得到的baseM值。baseM参数的说明请参考表1。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/GetBaseM.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetBaseM

获取 Tiling 计算得到的 baseM 值，对应 TCubeTiling 结构中的 baseM 参数，用于描述 Cube 矩阵乘单次迭代在 M 方向的基本块大小。
函数签名为 int32_t GetBaseM() const，无入参，返回值为 Tiling 计算结果。
约束：必须使用已创建的 MatmulApiTiling 对象调用，且需在完成 GetTiling 计算后再获取 baseM，否则返回值无效。
通常与 GetBaseK、GetBaseN 配合使用，分别对应 M、N、K 三个维度的 base 块大小，供后续 Kernel 内分块计算使用。
支持 Ascend 950PR/950DT、Atlas A2 与 Atlas A3 系列产品。

<!-- cannbot:related:start -->
## 相关

- [SetSingleRange](set_single_range.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《GetBaseM》明确“获取Tiling计算得到的baseM值。baseM参数的说明请参考表1。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [GetBaseK](get_base_k.md)（`same_topic`）：GetBaseM 与《GetBaseK》的实质衔接是：baseM 与 baseN/baseK 一起写入 TCubeTiling，由输入 shape、single shape 与 GetTiling 计算；Matmul 使用说明解释该块大小如何驱动 kernel 循环。
- [GetBaseN](get_base_n.md)（`same_topic`）：GetBaseM 与《GetBaseN》的实质衔接是：baseM 与 baseN/baseK 一起写入 TCubeTiling，由输入 shape、single shape 与 GetTiling 计算；Matmul 使用说明解释该块大小如何驱动 kernel 循环。
- [GetSingleShape](get_single_shape.md)（`same_topic`）：GetBaseM 与《GetSingleShape》的实质衔接是：baseM 与 baseN/baseK 一起写入 TCubeTiling，由输入 shape、single shape 与 GetTiling 计算；Matmul 使用说明解释该块大小如何驱动 kernel 循环。
- [GetTiling](get_tiling.md)（`same_topic`）：GetBaseM 与《GetTiling》的实质衔接是：baseM 与 baseN/baseK 一起写入 TCubeTiling，由输入 shape、single shape 与 GetTiling 计算；Matmul 使用说明解释该块大小如何驱动 kernel 循环。
- [Matmul Tiling类](matmul_tiling.md)（`same_topic`）：GetBaseM 与《Matmul Tiling类》的实质衔接是：baseM 与 baseN/baseK 一起写入 TCubeTiling，由输入 shape、single shape 与 GetTiling 计算；Matmul 使用说明解释该块大小如何驱动 kernel 循环。
- [Matmul Tiling类使用说明](matmul_tiling_usage.md)（`same_topic`）：GetBaseM 与《Matmul Tiling类使用说明》的实质衔接是：baseM 与 baseN/baseK 一起写入 TCubeTiling，由输入 shape、single shape 与 GetTiling 计算；Matmul 使用说明解释该块大小如何驱动 kernel 循环。
- [SetShape](set_shape.md)（`same_topic`）：GetBaseM 与《SetShape》的实质衔接是：baseM 与 baseN/baseK 一起写入 TCubeTiling，由输入 shape、single shape 与 GetTiling 计算；Matmul 使用说明解释该块大小如何驱动 kernel 循环。
- [TCubeTiling结构体](t_cube_tiling_struct.md)（`same_topic`）：GetBaseM 与《TCubeTiling结构体》的实质衔接是：baseM 与 baseN/baseK 一起写入 TCubeTiling，由输入 shape、single shape 与 GetTiling 计算；Matmul 使用说明解释该块大小如何驱动 kernel 循环。
<!-- cannbot:related:end -->
