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
