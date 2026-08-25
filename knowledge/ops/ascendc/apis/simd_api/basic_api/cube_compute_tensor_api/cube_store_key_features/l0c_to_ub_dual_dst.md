---
type: API
title: L0C Buffer到Unified Buffer双目标模式
description: L0C Buffer到Unified Buffer双目标模式用于将同一AI Core内L0C Buffer的矩阵结果拆分后，同时写入两个Vector
  Core各自的Unified Buffer。一个AI Core内包含一个Cube Core和两个Vector Core，启用双目标模式后，源矩阵会按指定维度拆分为两部分，前半部分写入SUB
  BLOCK0，后半部分写入SUB BLOCK1。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_store_key_features/l0c_to_ub_dual_dst.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# L0C Buffer到Unified Buffer双目标模式

L0C Buffer到Unified Buffer双目标模式用于将同一AI Core内L0C Buffer的矩阵结果拆分后，同时写入两个Vector

本接口属于 Cube 矩阵计算接口。

约束：双目标模式仅支持L0C Buffer到Unified Buffer通路。；双目标模式支持普通搬运模式NZ2NZ和NZ2ND搬运场景。；按M维度拆分时，M必须为2的倍数。；按N维度拆分时，N必须为32的倍数。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
