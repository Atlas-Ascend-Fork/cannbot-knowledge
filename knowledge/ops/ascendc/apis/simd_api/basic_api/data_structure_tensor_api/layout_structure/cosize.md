---
type: API
title: Cosize（基础API）
description: 需要包含的头文件为：#include "tensor_api/tensor.h"。 Cosize表示Layout陪域（codomain）的跨度大小，即逻辑坐标经Layout映射为一维索引后，所有可能索引值所处区间的长度。Cosize和Coshape在扁平与嵌套Layout场景下等价。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/Cosize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Cosize（基础API）

表示 Layout 陪域的跨度大小，即逻辑坐标经 Layout 映射为一维索引后所有可能索引值所处区间的长度。与 Coshape 在扁平与嵌套 Layout 场景下等价。头文件 `tensor_api/tensor.h`。仅 950 支持。

<!-- cannbot:related:start -->
## 相关

- [Coshape](coshape.md)（`same_topic`）：“需要包含的头文件为：#include "tensor_api/tensor.h"。 Coshape表示Layout陪域（codomain）区间的标量大小，即逻辑坐标映射到一维索引后，所有可能的索引值构成的区间大小。其计算公式为：”与“表示 Layout 陪域的跨度大小，即逻辑坐标经 Layout 映射为一维索引后所有可能索引值所处区间的长度。与 Coshape 在扁平与嵌套 Layout 场景下等价。头文件 `tensor_api/tensor.h`。仅 950 支持。”提供双方正文证据。两卡定义同一 Layout 陪域区间/跨度，并由 Cosize 明确声明扁平与嵌套场景均与 Coshape 等价，可作为同一查询语义理解。
<!-- cannbot:related:end -->
