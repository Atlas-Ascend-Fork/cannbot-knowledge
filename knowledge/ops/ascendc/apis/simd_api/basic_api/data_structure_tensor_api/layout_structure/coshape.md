---
type: API
title: Coshape
description: 表示Layout陪域区间的标量大小，即逻辑坐标映射到一维索引后所有可能的索引值构成的区间大小。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/Coshape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Coshape

表示Layout陪域区间的标量大小，即逻辑坐标映射到一维索引后所有可能的索引值构成的区间大小。

需要包含的头文件为：#include "tensor_api/tensor.h"。 Coshape表示Layout陪域（codomain）区间的标量大小，即逻辑坐标映射到一维索引后，所有可能的索引值构成的区间大小。其计算公式为：

返回值：返回Layout的陪域（codomain）的形状。

约束：Is...必须为有效范围内的索引。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

<!-- cannbot:related:start -->
## 相关

- [Capacity（基础API）](capacity.md)（`related`）：Capacity 用布局的 stride/shape 评估存储容量，可与 Coshape 检查非紧凑布局是否存在空洞。
- [GetShape](get_shape.md)（`related`）：GetShape 返回逻辑定义域 shape，Coshape 返回映射后的陪域 shape，二者区分逻辑维度和物理索引范围。
- [Shape（基础API）](shape.md)（`related`）：CoShape 表示与 shape 对偶的坐标/余形结构，适合布局变换而非替代普通 Shape。
- [Cosize（基础API）](cosize.md)（`same_topic`）：Coshape说明表示Layout陪域区间的标量大小，即逻辑坐标映射到一维索引后所有可能的索引值构成的区间大小。
<!-- cannbot:related:end -->
