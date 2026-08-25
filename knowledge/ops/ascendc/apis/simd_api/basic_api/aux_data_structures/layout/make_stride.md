---
type: API
title: MakeStride
description: 将传入的数据打包成Stride数据结构。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Layout/MakeStride.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# MakeStride

构造Stride结构体的辅助函数。通过传入各维度步长创建Stride。函数原型提供1维到8维的构造重载。参数为各维度的stride值。返回Stride结构体。用于描述Tensor各维度的内存步长。

<!-- cannbot:related:start -->
## 相关

- [Crd2Idx](../coordinate/crd2_idx.md)（`related`）：Crd2Idx 消费 Layout 中的 stride，将多维坐标转换为线性地址，体现步长的直接用途。
- [Layout构造函数](layout_constructor.md)（`related`）：《Layout构造函数》说明根据输入的Shape和Stride对象，实例化Layout对象。；《MakeStride》说明将传入的数据打包成Stride数据结构。。二者在Layout由Shape与Stride构造，MakeLayout、GetShape/GetStride、Crd2Idx和is_layout共同定义其类型与索引合同上存在可执行的直接衔接。
- [MakeLayout](make_layout.md)（`related`）：MakeStride 生成的步长对象需与 Shape 一起传给 MakeLayout，形成完整内存布局。
- [MakeShape](make_shape.md)（`related`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《MakeStride》说明将传入的数据打包成Stride数据结构。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [layout](layout1.md)（`related`）：layout 与《MakeStride》的实质衔接是：Layout 同时承载 shape、stride 与 format，由 MakeLayout 构造并通过 Get/Set 访问；Crd2Idx、排布格式与 NDExtLayout 方向故障验证其寻址语义。
- [GetStride](get_stride.md)（`same_topic`）：GetStride 与《MakeStride》的实质衔接是：GetStride 从 Layout 读取 MakeStride 生成的维度步长，Crd2Idx 以该 stride 映射坐标；NDDMA stride=0 故障和 Layout 说明验证物理寻址边界。
<!-- cannbot:related:end -->
