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
