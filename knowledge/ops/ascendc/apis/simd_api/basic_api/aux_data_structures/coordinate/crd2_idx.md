---
type: API
title: Crd2Idx
description: 将多维坐标通过布局(Layout)转换为内存位置索引，Layout包含Shape和Stride信息。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Coordinate/Crd2Idx.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# Crd2Idx

将Coordinate坐标转换为Tensor中的线性索引（index）。给定多维坐标和Tensor的shape信息，计算对应的线性偏移量。

函数原型提供基于TensorDesc和基于shape数组的两种方式。参数包含coord输入坐标、tensorDesc或shape信息。返回值为线性索引。用于通过多维坐标定位Tensor元素。

<!-- cannbot:related:start -->
## 相关

- [Coordinate简介](coordinate_intro.md)（`related`）：Crd2Idx 消费 Coordinate 和布局信息得到线性偏移，直接把多维坐标结构落实为 Tensor 访存位置。
- [Coord（基础API）](../../data_structure_tensor_api/layout_structure/coord.md)（`related`）：焦点处理Coord 参与 Layout 坐标映射和 Tensor Slice 的用法；Crd2Idx正文说明“将多维坐标通过布局(Layout)转换为内存位置索引，Layout包含Shape和Stride信息”。候选把 Coord 构造、Layout 映射、Crd2Idx 与 Slice 的正文调用关系展开。
- [GetStride](../layout/get_stride.md)（`related`）：Crd2Idx 与《GetStride》的实质衔接是：Crd2Idx 用 Coordinate 与 Layout 的 shape/stride 计算线性索引，MakeCoord、Layout/TensorDesc 构造和 GetStride 提供两种重载所需的数据结构。
- [Layout构造函数](../layout/layout_constructor.md)（`related`）：《Layout构造函数》说明根据输入的Shape和Stride对象，实例化Layout对象。；《Crd2Idx》说明将多维坐标通过布局(Layout)转换为内存位置索引，Layout包含Shape和Stride信息。。二者在Layout由Shape与Stride构造，MakeLayout、GetShape/GetStride、Crd2Idx和is_layout共同定义其类型与索引合同上存在可执行的直接衔接。
- [Layout简介](../layout/layout_intro.md)（`related`）：Crd2Idx 消费 Layout 的 shape 和 stride，把多维 Coordinate 映射为线性索引，体现 Layout 的核心用途。
- [MakeShape](../layout/make_shape.md)（`related`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《Crd2Idx》说明将多维坐标通过布局(Layout)转换为内存位置索引，Layout包含Shape和Stride信息。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [MakeStride](../layout/make_stride.md)（`related`）：Crd2Idx 消费 Layout 中的 stride，将多维坐标转换为线性地址，体现步长的直接用途。
- [TensorDesc](../tensor_desc/tensor_desc.md)（`related`）：Crd2Idx 与《TensorDesc》的实质衔接是：Crd2Idx 用 Coordinate 与 Layout 的 shape/stride 计算线性索引，MakeCoord、Layout/TensorDesc 构造和 GetStride 提供两种重载所需的数据结构。
- [TensorDesc简介](../tensor_desc/tensor_desc_intro.md)（`related`）：Crd2Idx 与《TensorDesc简介》的实质衔接是：Crd2Idx 用 Coordinate 与 Layout 的 shape/stride 计算线性索引，MakeCoord、Layout/TensorDesc 构造和 GetStride 提供两种重载所需的数据结构。
- [Coordinate](coordinate.md)（`same_topic`）：Crd2Idx 与《Coordinate》的实质衔接是：Crd2Idx 用 Coordinate 与 Layout 的 shape/stride 计算线性索引，MakeCoord、Layout/TensorDesc 构造和 GetStride 提供两种重载所需的数据结构。
- [MakeCoord](make_coord.md)（`same_topic`）：Crd2Idx 与《MakeCoord》的实质衔接是：Crd2Idx 用 Coordinate 与 Layout 的 shape/stride 计算线性索引，MakeCoord、Layout/TensorDesc 构造和 GetStride 提供两种重载所需的数据结构。
- [MakeLayout](../layout/make_layout.md)（`same_topic`）：MakeLayout 与《Crd2Idx》的实质衔接是：MakeLayout 将 MakeShape 和 MakeStride 的结果组合为 Layout；直接构造函数是等价构造路径，Crd2Idx 以该 Layout 做坐标到地址映射，Layout 概念卡解释 shape/stride 的内存契约。
- [layout](../layout/layout1.md)（`same_topic`）：layout 与《Crd2Idx》的实质衔接是：Layout 同时承载 shape、stride 与 format，由 MakeLayout 构造并通过 Get/Set 访问；Crd2Idx、排布格式与 NDExtLayout 方向故障验证其寻址语义。
<!-- cannbot:related:end -->
