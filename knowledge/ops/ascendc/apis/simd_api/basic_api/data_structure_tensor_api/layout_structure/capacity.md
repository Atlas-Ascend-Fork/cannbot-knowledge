---
type: API
title: Capacity（基础API）
description: 需要包含的头文件为：#include "tensor_api/tensor.h"。 Capacity用于计算Layout所需的实际内存容量。
  与Size（有效元素个数）不同，Capacity包含了因非连续步长导致的无效数据区域。对于连续排列（stride紧凑），Capacity与Size相等；对于有间隔的排列，Capacity通常大于Size。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/Capacity.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Capacity（基础API）

计算 Layout 所需的实际内存容量，包含因非连续步长导致的无效数据区域。连续排列时 Capacity 与 Size 相等，有间隔时 Capacity 通常大于 Size。头文件 `tensor_api/tensor.h`。仅 950 支持。

<!-- cannbot:related:start -->
## 相关

- [Coshape](coshape.md)（`related`）：Capacity 用布局的 stride/shape 评估存储容量，可与 Coshape 检查非紧凑布局是否存在空洞。
- [Cosize（基础API）](cosize.md)（`related`）：Cosize（基础API）说明需要包含的头文件为：#include "tensor_api/tensor.h"。 Cosize表示Layout陪域（codomain）的跨度大小，即逻辑坐标经Layout映射为一维索引后，所有可能索引值所处区间的长度。Cosize和Coshape在扁平与嵌套Layout场景下等价；对Capacity（基础API）而言，Capacity 是 Layout 可寻址元素容量，需用 Cosize/Size 的计算口径和 Layout 的 Shape/Stride 定义辨清含 padding 的内存范围。
- [Layout数据结构](layout_structure.md)（`related`）：Layout数据结构说明TensorAPI Layout 数据结构集，包含 Layout、Shape、Stride、Coord 及 MakeLayout、GetShape 等相关接口；对Capacity（基础API）而言，Capacity 是 Layout 可寻址元素容量，需用 Cosize/Size 的计算口径和 Layout 的 Shape/Stride 定义辨清含 padding 的内存范围。
- [Stride（基础API）](stride.md)（`related`）：Capacity 由 shape/stride 共同决定物理覆盖范围，可用于验证自定义 Stride 是否导致越界或空洞。
- [基础APISize](size.md)（`related`）：基础APISize说明返回 Layout 的有效元素数量，并支持通过模板索引选择要统计的维度；对Capacity（基础API）而言，Capacity 是 Layout 可寻址元素容量，需用 Cosize/Size 的计算口径和 Layout 的 Shape/Stride 定义辨清含 padding 的内存范围。
- [基础API工具函数](../utils/tool_functions.md)（`related`）：工具函数常用于验证 layout 的物理容量和映射。
<!-- cannbot:related:end -->
