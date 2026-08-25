---
type: API
title: SatMode
description: SatMode 用于设置Cast类型转换饱和与不饱和模式。enum class SatMode { UNKNOWN = -1, NO_SAT,
  SAT };&bull;&nbsp;&nbsp;UNKNOWN：当转换类型不支持SatMode时，选择该模式；&bull;&nbsp;&nbsp;NO_SAT：不饱和模式；&bull;&nbsp;&nbsp;SAT：饱和模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/aux_data_types/SatMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# SatMode

SatMode 用于设置Cast类型转换饱和与不饱和模式。enum class SatMode { UNKNOWN = -1, NO_SAT,

本接口属于 Reg 矢量计算辅助数据类型定义。

# SatMode | 参数名 | 描述 | | :-- | :-- | | SatMode | 用于设置Cast类型转换饱和与不饱和模式。 enum class SatMode { UNKNOWN = -1, NO_SAT, SAT }; • UNKNOWN：当转换类型不支持SatMode时，选择该模式； • NO_SAT：不饱和模式； • SAT：饱和模式。 |

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
