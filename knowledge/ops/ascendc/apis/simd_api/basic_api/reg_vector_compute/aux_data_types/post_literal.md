---
type: API
title: PostLiteral
description: 枚举类型，用于控制是否开启UB地址自动更新功能，含NORMAL不更新和UPDATE更新两种模式。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.execution_unit.vector
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/aux_data_types/PostLiteral.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
---

# PostLiteral<a name="ZH-CN_TOPIC_0000001956862301"></a>

| 参数名 | 描述 |
| :-- | :-- | 
| PostLiteral | 用于控制是否开启Unified Buffer（UB）地址自动更新功能（post update）。<br>enum class PostLiteral { <br>    POST_MODE_NORMAL, <br>    POST_MODE_UPDATE <br>};<br>&bull;&nbsp;&nbsp;POST_MODE_NORMAL：POST_MODE_NORMAL场景使用，UB操作数地址不更新。连续非对齐搬入（LoadUnAlign）不支持POST_MODE_NORMAL模式；<br>&bull;&nbsp;&nbsp;POST_MODE_UPDATE：POST_MODE_UPDATE场景使用，UB地址同时作为输入和输出，每次调用会更新。 |

```cpp
enum class PostLiteral {
    POST_MODE_NORMAL,
    POST_MODE_UPDATE
};
```
