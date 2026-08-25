---
type: API
title: Layout简介
description: Layout数据结构是描述多维张量内存布局的基础模板类，通过编译时的形状（Shape）和步长（Stride）信息，实现逻辑坐标空间到一维内存地址空间的映射，为复杂张量操作和硬件优化提供基础支持。借助模板元编程技术，该类在编译时完成计算和代码生成，从而降低运行时开销。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Layout/Layout_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---


# Layout简介

Layout是描述Tensor数据排布的结构体，包含shape（各维度大小）、stride（各维度步长）和format（数据格式）等信息。Layout用于描述Tensor在内存中的实际排布方式，支持ND、NZ等格式。通过MakeLayout构造Layout，可指定shape、stride和format。Layout支持通过GetShape获取形状、GetStride获取步长、通过operator==判断两个Layout是否相等。Layout与TensorDesc/TensorTrait配合使用，描述Tensor的完整信息。

<!-- cannbot:related:start -->
## 相关

- [Coordinate简介](../coordinate/coordinate_intro.md)（`related`）：Layout 提供 Shape 和 Stride，正是 Crd2Idx 将 Coordinate 线性化所需的内存排布语义。
- [Crd2Idx](../coordinate/crd2_idx.md)（`related`）：Crd2Idx 消费 Layout 的 shape 和 stride，把多维 Coordinate 映射为线性索引，体现 Layout 的核心用途。
- [GetStride](get_stride.md)（`related`）：GetStride 读取 Layout 的地址步长，与 shape 一起决定逻辑坐标到线性地址的映射。
- [Layout构造函数](layout_constructor.md)（`related`）：《Layout构造函数》说明根据输入的Shape和Stride对象，实例化Layout对象。；《Layout简介》说明Layout数据结构是描述多维张量内存布局的基础模板类，通过编译时的形状（Shape）和步长（Stride）信息，实现逻辑坐标空间到一维内存地址空间的映射，为复杂张量操作和硬件优化提供基础支持。借助模板元编程技术，该类在编译时完成计算和代码生成，从而降低运行时开销。。二者在Layout由Shape与Stride构造，MakeLayout、GetShape/GetStride、Crd2Idx和is_layout共同定义其类型与索引合同上存在可执行的直接衔接。
- [MakeShape](make_shape.md)（`related`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《Layout简介》说明Layout数据结构是描述多维张量内存布局的基础模板类，通过编译时的形状（Shape）和步长（Stride）信息，实现逻辑坐标空间到一维内存地址空间的映射，为复杂张量操作和硬件优化提供基础支持。借助模板元编程技术，该类在编译时完成计算和代码生成，从而降低运行时开销。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [is_layout](is_layout.md)（`related`）：《is_layout》说明判断输入的数据结构是否为Layout数据结构，可通过检查其成员常量value的值来判断。当value为true时，表示输入的数据结构是Layout类型；反之则为非Layout类型。；《Layout简介》说明Layout数据结构是描述多维张量内存布局的基础模板类，通过编译时的形状（Shape）和步长（Stride）信息，实现逻辑坐标空间到一维内存地址空间的映射，为复杂张量操作和硬件优化提供基础支持。借助模板元编程技术，该类在编译时完成计算和代码生成，从而降低运行时开销。。二者在is_layout用于识别Layout类型，构造、Shape/Stride访问和MakeLayout是其直接类型契约上存在可执行的直接衔接。
- [GetShape](get_shape.md)（`same_topic`）：Layout 由 Shape 与 Stride 共同描述逻辑维度到内存地址映射，GetShape 提取其中的逻辑维度部分。
- [Layout（辅助数据结构）](layout.md)（`same_topic`）：简介解释 Layout 通过编译期 Shape 与 Stride 完成坐标到线性地址映射，补足对象总览背后的内存语义。
- [MakeLayout](make_layout.md)（`same_topic`）：Layout 简介说明 shape、stride 与 format 的抽象，MakeLayout 是据此构造该对象的入口。
- [layout](layout1.md)（`same_topic`）：layout 与《Layout简介》的实质衔接是：Layout 同时承载 shape、stride 与 format，由 MakeLayout 构造并通过 Get/Set 访问；Crd2Idx、排布格式与 NDExtLayout 方向故障验证其寻址语义。
- [运算符重载](operator_overloading.md)（`same_topic`）：“运算符重载”处理重载运算符\(\)，内部实现为调用Crd2Idx接口，将多维坐标（Coordinate）通过布局（Layout）转换为内存位置索引（Index）。；“Layout简介”明确Layout数据结构是描述多维张量内存布局的基础模板类，通过编译时的形状（Shape）和步长（Stride）信息，实现逻辑坐标空间到一维内存地址空间的映射，为复杂张量操作和硬件优化提供基础支持。借助模板元编程技术，该类在编译时完成计算和代码生成，从而降低运行时开销。。实质衔接：operator== 比较 Layout 的 shape、stride、format；Layout 简介定义这些属性及其内存布局语义。
<!-- cannbot:related:end -->
