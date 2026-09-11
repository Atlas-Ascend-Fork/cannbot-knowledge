---
type: API
title: SatMode
description: SatMode 用于设置 Cast 类型转换的饱和与不饱和模式，包括 UNKNOWN、NO_SAT 和 SAT。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.execution_unit.vector
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/aux_data_types/SatMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
---

# SatMode<a name="ZH-CN_TOPIC_0000001956862301"></a>

| 参数名 | 描述 |
| :-- | :-- | 
| SatMode | 用于设置Cast类型转换饱和与不饱和模式。<br>enum class SatMode { <br>    UNKNOWN = -1, <br>    NO_SAT, <br>    SAT <br>};<br>&bull;&nbsp;&nbsp;UNKNOWN：当转换类型不支持SatMode时，选择该模式；<br>&bull;&nbsp;&nbsp;NO_SAT：不饱和模式；<br>&bull;&nbsp;&nbsp;SAT：饱和模式。 |

```cpp
enum class SatMode {
    UNKNOWN = -1,
    NO_SAT,
    SAT
};
```
