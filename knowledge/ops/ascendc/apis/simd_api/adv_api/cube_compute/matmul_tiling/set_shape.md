---
type: API
title: SetShape
description: 设置Matmul计算的形状m、n、k，可为完整矩阵或局部矩阵，支持传入-1按原始形状计算
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetShape

设置Matmul计算的形状m、n、k，该形状可以为原始完整矩阵或其局部矩阵，单位为元素。该形状的矩阵乘可以由单核或多核计算完成。 使用本接口时，有两种参数传入方式： - 传入Matmul计算的形状m、n、k，调用GetTiling接口时，按照m、n、k计算并返回Tiling参数。

参数：
- m：输入设置Matmul计算的M方向大小，单位为元素。
- n：输入设置Matmul计算的N方向大小，单位为元素。
- k：输入设置Matmul计算的K方向大小，单位为元素。

返回值：-1表示设置失败；0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [GetShapeInfo](../../../basic_api/data_structures/global_tensor/get_shape_info.md)（`related`）：GetShapeInfo 与《SetShape》的实质衔接是：GetShapeInfo 只有在对应 GlobalTensor 已 SetShapeInfo 后才有效；ShapeInfo、SetGlobalBuffer 与 tensor 子视图共同约束 shape 元数据生命周期。
- [GetTiling](get_tiling.md)（`related`）：SetShape 只写入 Tiling 输入，最终由 GetTiling 读取这些 M/N/K 配置并产出 TCubeTiling；二者构成设置到求解的调用链。
- [SetOrgShape](set_org_shape.md)（`related`）：SetShape 的 -1 取值需要回落到原始 M/N/K，而 SetOrgShape 正是提供原始完整 shape 的契约；未设置原始 shape 会使 -1 语义缺少来源。
- [SetSingleRange](set_single_range.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《SetShape》明确“设置Matmul计算的形状m、n、k，可为完整矩阵或局部矩阵，支持传入-1按原始形状计算”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [SetSingleShape](set_single_shape.md)（`related`）：SetShape 提供完整 M/N/K，SetSingleShape 再约束单核 M/N/K；多核 Matmul Tiling 必须区分完整问题规模与单核切分规模。
- [GetBaseM](get_base_m.md)（`same_topic`）：GetBaseM 与《SetShape》的实质衔接是：baseM 与 baseN/baseK 一起写入 TCubeTiling，由输入 shape、single shape 与 GetTiling 计算；Matmul 使用说明解释该块大小如何驱动 kernel 循环。
<!-- cannbot:related:end -->
