---
type: API
title: SetFmatrixBitMode
description: 调用LoadData（卷积数据搬运）时以位域方式设置FeatureMap的属性描述，包括l1H、l1W和padList，需在LoadData接口前调用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_load_aux_config/SetFmatrixBitMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# SetFmatrixBitMode

SetFmatrix 的 BitMode 变体，以位域方式设置 LoadData（卷积数据搬运）的 FeatureMap 属性描述。当 LoadData 模板参数 isSetFMatrix 为 false 时使用。用于追求极致 Scalar 性能的场景。

参数：param 为 SetFMatrixBitModeParams 结构体（含 l1H、l1W、padList 等位域配置）；fmatrixMode 为 FmatrixMode 类型，当前仅支持 FMATRIX_LEFT。仅 Ascend 950PR/950DT 支持。
