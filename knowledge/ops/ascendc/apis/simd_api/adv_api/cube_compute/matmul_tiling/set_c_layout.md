---
type: API
title: SetCLayout
description: 设置C矩阵的Layout轴信息，包括B、S、N、G、D轴。对于BSNGD、SBNGD、BNGS1S2 Layout格式，调用IterateBatch接口之前，需要在Host侧Tiling实现中通过本接口设置C矩阵的Layout轴信息。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetCLayout.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetCLayout

设置C矩阵的Layout轴信息，包括B、S、N、G、D轴。对于BSNGD、SBNGD、BNGS1S2 Layout格式，调用IterateBatch接口之前，需要在Host侧Tiling实现中通过本接口设置C矩阵的Layout轴信息。

参数：
- b：输入C矩阵Layout的B轴信息
- s：输入C矩阵Layout的S轴信息
- n：输入C矩阵Layout的N轴信息
- g：输入C矩阵Layout的G轴信息
- d：输入C矩阵Layout的D轴信息

返回值：-1表示设置失败； 0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [IterateBatch](../matmul_kernel/iterate_batch.md)（`related`）：SetCLayout 文档明确要求 BSNGD、SBNGD、BNGS1S2 布局在调用 IterateBatch 前设置 C 的 B/S/N/G/D 轴信息。
- [SetBLayout](set_b_layout.md)（`related`）：《SetCLayout》明确“设置C矩阵的Layout轴信息，包括B、S、N、G、D轴。对于BSNGD、SBNGD、BNGS1S2 Layout格式，调用IterateBatch接口之前，需要在Host侧Tiling实现中通过本接口设置C矩阵的Layout轴信息。”；它与《SetBLayout》的“设置B矩阵的Layout轴信息，包括B、S、N、G、D轴。对于BSNGD、SBNGD、BNGS1S2 Layout格式，调用IterateBatch接口之前，需要在Host侧Tiling实现中通过本接口设置B矩阵的Layout轴信息。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
