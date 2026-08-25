---
type: API
title: MakeShape
description: 将传入的数据打包成Shape数据结构。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Layout/MakeShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# MakeShape

构造Shape结构体的辅助函数。通过传入各维度大小创建Shape。函数原型提供1维到8维的构造重载。参数为各维度的size值。返回Shape结构体。用于快速创建Tensor形状描述。

<!-- cannbot:related:start -->
## 相关

- [Crd2Idx](../coordinate/crd2_idx.md)（`related`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《Crd2Idx》说明将多维坐标通过布局(Layout)转换为内存位置索引，Layout包含Shape和Stride信息。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [GetShape](get_shape.md)（`related`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《GetShape》说明返回描述张量形状的Shape对象。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [GetStride](get_stride.md)（`related`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《GetStride》说明返回描述内存访问步长的Stride对象，与Shape的维度信息一一对应。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [Layout数据结构](../../data_structure_tensor_api/layout_structure/layout_structure.md)（`related`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《Layout数据结构》说明TensorAPI Layout 数据结构集，包含 Layout、Shape、Stride、Coord 及 MakeLayout、GetShape 等相关接口。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [Layout构造函数](layout_constructor.md)（`related`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《Layout构造函数》说明根据输入的Shape和Stride对象，实例化Layout对象。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [Layout简介](layout_intro.md)（`related`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《Layout简介》说明Layout数据结构是描述多维张量内存布局的基础模板类，通过编译时的形状（Shape）和步长（Stride）信息，实现逻辑坐标空间到一维内存地址空间的映射，为复杂张量操作和硬件优化提供基础支持。借助模板元编程技术，该类在编译时完成计算和代码生成，从而降低运行时开销。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [MakeCoord](../coordinate/make_coord.md)（`related`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《MakeCoord》说明将传入的数据打包成Coord数据结构。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [MakeLayout](make_layout.md)（`related`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《MakeLayout》说明将传入的Shape和Stride数据打包成Layout数据结构。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [MakeStride](make_stride.md)（`related`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《MakeStride》说明将传入的数据打包成Stride数据结构。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [Shape（基础API）](../../data_structure_tensor_api/layout_structure/shape.md)（`related`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《Shape（基础API）》说明定义张量各维度的逻辑大小，并与 Stride 组合形成支持层次化表述的 Layout。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [is_layout](is_layout.md)（`related`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《is_layout》说明判断输入的数据结构是否为Layout数据结构，可通过检查其成员常量value的值来判断。当value为true时，表示输入的数据结构是Layout类型；反之则为非Layout类型。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [layout](layout1.md)（`related`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《layout》说明获取Layout实例化对象。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [MakeShape](../../data_structure_tensor_api/layout_structure/make_shape.md)（`same_topic`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《MakeShape》说明构造Shape对象，用于描述数据的逻辑形状。支持传入多个维度值，也支持传入嵌套的Shape子结构以构造层次化Shape。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
<!-- cannbot:related:end -->
