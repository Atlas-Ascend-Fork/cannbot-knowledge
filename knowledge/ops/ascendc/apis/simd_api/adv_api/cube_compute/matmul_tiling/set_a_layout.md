---
type: API
title: SetALayout
description: 设置A矩阵的Layout轴信息，包括B、S、N、G、D轴。对于BSNGD、SBNGD、BNGS1S2 Layout格式，调用IterateBatch接口之前，需要在Host侧Tiling实现中通过本接口设置A矩阵的Layout轴信息。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetALayout.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetALayout

设置A矩阵的Layout轴信息，包括B、S、N、G、D轴。对于BSNGD、SBNGD、BNGS1S2 Layout格式，调用IterateBatch接口之前，需要在Host侧Tiling实现中通过本接口设置A矩阵的Layout轴信息。

参数：
- b：输入A矩阵Layout的B轴信息
- s：输入A矩阵Layout的S轴信息
- n：输入A矩阵Layout的N轴信息
- g：输入A矩阵Layout的G轴信息
- d：输入A矩阵Layout的D轴信息

返回值：-1表示设置失败； 0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [Matmul Tiling类使用说明](matmul_tiling_usage.md)（`related`）：“用户只需要传入A/B/C矩阵的Position位置、Format格式和DType数据类型等信息，调用API接口，即可获取到Init中TCubeTiling结构体中的相关参数。”与“设置A矩阵的Layout轴信息，包括B、S、N、G、D轴。对于BSNGD、SBNGD、BNGS1S2 Layout格式，调用IterateBatch接口之前，需要在Host侧Tiling实现中通过本接口设置A矩阵的Layout轴信息。”提供双方正文证据。通用流程要求先提供矩阵元数据，SetALayout 补充三类 Batch Layout 在 IterateBatch 前必须设置的 B/S/N/G/D 轴信息，形成特殊布局的调用前置条件。
<!-- cannbot:related:end -->
