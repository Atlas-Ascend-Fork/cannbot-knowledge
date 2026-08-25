---
type: API
title: MakeShape
description: 构造Shape对象，用于描述数据的逻辑形状。支持传入多个维度值，也支持传入嵌套的Shape子结构以构造层次化Shape。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/MakeShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# MakeShape

构造 Shape 对象描述数据逻辑形状。支持传入多个维度值，也支持嵌套 Shape 子结构构造层次化 Shape。头文件 `tensor_api/tensor.h`。仅 950 支持。

<!-- cannbot:related:start -->
## 相关

- [MakeLayout](make_layout.md)（`related`）：MakeLayout 明确以 MakeShape 产出的 Shape 和 Stride 构造排布对象，直接给出 focal 结果的下游使用点。
- [MakePatternLayout](make_pattern_layout.md)（`related`）：MakePatternLayout 与《MakeShape》的衔接是：MakePatternLayout 把 LayoutPattern/Trait 附着到由 Shape、Stride 构成的 Layout；GetLayoutPattern 和 MakeLayout 是读取与构造同一元数据的配套步骤，方向不匹配会造成矩阵布局解释错误。
- [MakeStride](make_stride.md)（`related`）：Shape 描述逻辑维度、Stride 描述各维内存步长，二者是 MakeLayout 的两个互补输入。
- [GetShape](get_shape.md)（`same_topic`）：MakeShape 构造随后由 GetShape 读取的 Shape 元组，形成创建和查询契约。
- [MakeShape](../../aux_data_structures/layout/make_shape.md)（`same_topic`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《MakeShape》说明构造Shape对象，用于描述数据的逻辑形状。支持传入多个维度值，也支持传入嵌套的Shape子结构以构造层次化Shape。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [Shape（基础API）](shape.md)（`same_topic`）：MakeShape 构造 Shape 对象，是类型页所描述 shape 的主要创建入口。
<!-- cannbot:related:end -->
