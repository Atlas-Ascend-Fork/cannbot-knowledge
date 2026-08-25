---
type: API
title: 基础API工具函数
description: TensorAPI 基础 API 工具函数集，当前提供 GetLayoutPattern 接口用于查询 Layout 模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/utils/tool_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 基础API工具函数

提供 GetLayoutPattern 接口，用于从 Layout 类型中提取其 LayoutPattern 类型信息。该接口为试验接口，不保证后续兼容性。

对于 MakeLayout 构造的 Layout，GetLayoutPattern 会根据 Shape 和 Stride 的类型结构自动推导可识别的 LayoutPattern（如 NZLayoutPtn、NDLayoutPtn）；当运行时数值未编码到类型中、无法根据类型唯一识别时返回 Std::ignore_t。仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Capacity（基础API）](../layout_structure/capacity.md)（`related`）：工具函数常用于验证 layout 的物理容量和映射。
- [MakePatternLayout](../layout_structure/make_pattern_layout.md)（`related`）：GetLayoutPattern 的结果可用于构造/验证 PatternLayout。
- [GetLayoutPattern](get_layout_pattern.md)（`same_topic`）：该工具从 Layout 推导 pattern，是工具总页的具体入口。
<!-- cannbot:related:end -->
