---
type: API
title: MaskMergeMode
description: 枚举类型，用于指定寄存器数据写入模式，包括ZEROING置零和MERGING保留原值两种模式。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.execution_unit.vector
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/aux_data_types/MaskMergeMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
---

# MaskMergeMode<a name="ZH-CN_TOPIC_0000001956862301"></a>

| 参数名 | 描述 |
| :-- | :-- | 
| MaskMergeMode | 用于指定写入寄存器数据模式。<br>enum class MaskMergeMode { <br>    UNKNOWN, <br>    MERGING, <br>    ZEROING <br>};<br>&bull;&nbsp;&nbsp;UNKNOWN：当转换类型不支持MaskMergeMode时，选择该模式；<br>&bull;&nbsp;&nbsp;ZEROING：mask未选择的元素在dst中置零；<br>&bull;&nbsp;&nbsp;MERGING：mask未选择的元素对应dst元素中保留dst原值。 |

```cpp
enum class MaskMergeMode {
    UNKNOWN,
    MERGING,
    ZEROING
};
```

以Duplicate接口为例，ZEROING和MERGING模式图示如下：

**图1** ZEROING/MERGING对比<a id="fig1"></a>

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zeroing_merging_comparison.png "ZEROING/MERGING对比")
