---
type: API
title: GetBaseK
description: 获取Tiling计算得到的baseK值。baseK参数的说明请参考表1。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/GetBaseK.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetBaseK

获取 Tiling 计算得到的 baseK 值，对应 TCubeTiling 结构中的 baseK 参数，用于描述 Cube 矩阵乘单次迭代在 K 方向的基本块大小。
函数签名为 int32_t GetBaseK() const，无入参，返回值为 Tiling 计算结果。
约束：必须使用已创建的 MatmulApiTiling 对象调用，且需在完成 GetTiling 计算后再获取 baseK，否则返回值无效。
通常与 GetBaseM、GetBaseN 配合使用，分别对应 M、N、K 三个维度的 base 块大小，供后续 Kernel 内分块计算使用。
支持 Ascend 950PR/950DT、Atlas A2 与 Atlas A3 系列产品。

<!-- cannbot:related:start -->
## 相关

- [GetBaseN](get_base_n.md)（`related`）：GetBaseK 与 GetBaseN 同属 GetTiling 后的结果回读，前者确定归约块、后者确定输出列块，Kernel 分块计算需同时消费这两个维度。
- [GetTiling](get_tiling.md)（`related`）：GetTiling 求解完成后 BaseK 才是最终硬件可用切分值。
- [SetFixSplit](set_fix_split.md)（`related`）：SetFixSplit 固定 M/N/K 切分，GetBaseK 用于读取最终生效的 K tile。
- [SetSingleRange](set_single_range.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《GetBaseK》明确“获取Tiling计算得到的baseK值。baseK参数的说明请参考表1。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [TCubeTiling结构体](t_cube_tiling_struct.md)（`related`）：BaseK 最终写入 TCubeTiling 并由 Kernel 消费。
- [GetBaseM](get_base_m.md)（`same_topic`）：GetBaseM 与《GetBaseK》的实质衔接是：baseM 与 baseN/baseK 一起写入 TCubeTiling，由输入 shape、single shape 与 GetTiling 计算；Matmul 使用说明解释该块大小如何驱动 kernel 循环。
- [GetSingleShape](get_single_shape.md)（`same_topic`）：GetSingleShape 与《GetBaseK》的实质衔接是：GetSingleShape 返回 GetTiling 计算出的单核 M/N/K，必须与 SetSingleShape/Range、baseM/N/K、coreNum 和 TCubeTiling 字段保持一致。
<!-- cannbot:related:end -->
