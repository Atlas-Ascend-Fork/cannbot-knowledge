---
type: API
title: Layout构造函数
description: 根据输入的Shape和Stride对象，实例化Layout对象。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Layout/Layout_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---


# Layout构造函数

Layout提供多种构造方式：默认构造（空Layout）、通过shape和stride构造、通过其他Layout拷贝构造等。构造后可通过SetShape/SetStride等方法修改属性。Layout构造参数可包含shape数组、stride数组、format格式等。构造的Layout用于描述Tensor的数据排布，传递给TensorDesc或TensorTrait使用。

<!-- cannbot:related:start -->
## 相关

- [Crd2Idx](../coordinate/crd2_idx.md)（`related`）：《Layout构造函数》说明根据输入的Shape和Stride对象，实例化Layout对象。；《Crd2Idx》说明将多维坐标通过布局(Layout)转换为内存位置索引，Layout包含Shape和Stride信息。。二者在Layout由Shape与Stride构造，MakeLayout、GetShape/GetStride、Crd2Idx和is_layout共同定义其类型与索引合同上存在可执行的直接衔接。
- [GetShape](get_shape.md)（`related`）：《Layout构造函数》说明根据输入的Shape和Stride对象，实例化Layout对象。；《GetShape》说明返回描述张量形状的Shape对象。。二者在Layout由Shape与Stride构造，MakeLayout、GetShape/GetStride、Crd2Idx和is_layout共同定义其类型与索引合同上存在可执行的直接衔接。
- [GetStride](get_stride.md)（`related`）：《Layout构造函数》说明根据输入的Shape和Stride对象，实例化Layout对象。；《GetStride》说明返回描述内存访问步长的Stride对象，与Shape的维度信息一一对应。。二者在Layout由Shape与Stride构造，MakeLayout、GetShape/GetStride、Crd2Idx和is_layout共同定义其类型与索引合同上存在可执行的直接衔接。
- [Layout简介](layout_intro.md)（`related`）：《Layout构造函数》说明根据输入的Shape和Stride对象，实例化Layout对象。；《Layout简介》说明Layout数据结构是描述多维张量内存布局的基础模板类，通过编译时的形状（Shape）和步长（Stride）信息，实现逻辑坐标空间到一维内存地址空间的映射，为复杂张量操作和硬件优化提供基础支持。借助模板元编程技术，该类在编译时完成计算和代码生成，从而降低运行时开销。。二者在Layout由Shape与Stride构造，MakeLayout、GetShape/GetStride、Crd2Idx和is_layout共同定义其类型与索引合同上存在可执行的直接衔接。
- [MakeShape](make_shape.md)（`related`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《Layout构造函数》说明根据输入的Shape和Stride对象，实例化Layout对象。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [MakeStride](make_stride.md)（`related`）：《Layout构造函数》说明根据输入的Shape和Stride对象，实例化Layout对象。；《MakeStride》说明将传入的数据打包成Stride数据结构。。二者在Layout由Shape与Stride构造，MakeLayout、GetShape/GetStride、Crd2Idx和is_layout共同定义其类型与索引合同上存在可执行的直接衔接。
- [is_layout](is_layout.md)（`related`）：《Layout构造函数》说明根据输入的Shape和Stride对象，实例化Layout对象。；《is_layout》说明判断输入的数据结构是否为Layout数据结构，可通过检查其成员常量value的值来判断。当value为true时，表示输入的数据结构是Layout类型；反之则为非Layout类型。。二者在Layout由Shape与Stride构造，MakeLayout、GetShape/GetStride、Crd2Idx和is_layout共同定义其类型与索引合同上存在可执行的直接衔接。
- [Layout（辅助数据结构）](layout.md)（`same_topic`）：《Layout构造函数》说明根据输入的Shape和Stride对象，实例化Layout对象。；《Layout（辅助数据结构）》说明Layout 辅助数据结构用于描述张量数据排布，提供构造函数、Shape/Stride 操作与 MakeLayout 等接口。。二者在Layout由Shape与Stride构造，MakeLayout、GetShape/GetStride、Crd2Idx和is_layout共同定义其类型与索引合同上存在可执行的直接衔接。
- [MakeLayout](make_layout.md)（`same_topic`）：《Layout构造函数》说明根据输入的Shape和Stride对象，实例化Layout对象。；《MakeLayout》说明将传入的Shape和Stride数据打包成Layout数据结构。。二者在Layout由Shape与Stride构造，MakeLayout、GetShape/GetStride、Crd2Idx和is_layout共同定义其类型与索引合同上存在可执行的直接衔接。
- [SetLayout](../tensor_trait/set_layout.md)（`same_topic`）：Layout构造函数说明根据输入的Shape和Stride对象，实例化Layout对象。
- [layout](layout1.md)（`same_topic`）：《Layout构造函数》说明根据输入的Shape和Stride对象，实例化Layout对象。；《layout》说明获取Layout实例化对象。。二者在Layout由Shape与Stride构造，MakeLayout、GetShape/GetStride、Crd2Idx和is_layout共同定义其类型与索引合同上存在可执行的直接衔接。
<!-- cannbot:related:end -->
