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
