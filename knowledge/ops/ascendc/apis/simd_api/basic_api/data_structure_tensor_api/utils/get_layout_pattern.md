---
type: API
title: GetLayoutPattern
description: 需要包含的头文件为：#include "tensor_api/tensor.h"。 GetLayoutPattern用于从Layout类型中提取其LayoutPattern类型信息。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/utils/GetLayoutPattern.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# GetLayoutPattern

需要包含的头文件为：#include "tensor_api/tensor.h"。 GetLayoutPattern用于从Layout类型中提取其LayoutPattern类型信息。

需要包含的头文件为：#include "tensor_api/tensor.h"。 GetLayoutPattern用于从Layout类型中提取其LayoutPattern类型信息。

返回值：若T包含Layout布局模式信息，则返回对应的LayoutPattern类型。 若T为MakeLayout构造的Layout，GetLayoutPattern会根据Shape和Stride的类型结构自动推导可识别的LayoutPattern；无法根据类型唯一识别时返回Std::ignore_t。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

<!-- cannbot:related:start -->
## 相关

- [noTrans extract 与 NDExtLayoutPtn 方向不匹配](../../../../../runbooks/precision/notrans_extract_ndextlayoutptn.md)（`exemplifies`）：故障根因落在 NDExtLayoutPtn 的读取方向与 noTrans 行序 extract 不一致；GetLayoutPattern 提供读取实际 LayoutPattern 的接口，可用于在路由前验证方向契约。
- [MakeLayout](../layout_structure/make_layout.md)（`related`）：MakeLayout 可按 shape/stride 推导 LayoutPattern，GetLayoutPattern 用于核验推导结果或识别歧义返回 ignore。
- [MakePatternLayout](../layout_structure/make_pattern_layout.md)（`related`）：MakePatternLayout 与《GetLayoutPattern》的衔接是：MakePatternLayout 把 LayoutPattern/Trait 附着到由 Shape、Stride 构成的 Layout；GetLayoutPattern 和 MakeLayout 是读取与构造同一元数据的配套步骤，方向不匹配会造成矩阵布局解释错误。
- [基础API工具函数](tool_functions.md)（`same_topic`）：该工具从 Layout 推导 pattern，是工具总页的具体入口。
<!-- cannbot:related:end -->
