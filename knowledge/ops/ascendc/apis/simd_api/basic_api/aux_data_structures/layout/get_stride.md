---
type: API
title: GetStride
description: 返回描述内存访问步长的Stride对象，与Shape的维度信息一一对应。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Layout/GetStride.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# GetStride

获取Layout的Stride信息。返回Layout中描述的各维度步长。函数原型：Stride GetStride() const。返回Stride结构体，包含各维度步长。用于查询Tensor的内存步长信息。

<!-- cannbot:related:start -->
## 相关

- [NDDMA 最内层 srcStride=0 广播读越界](../../../../../runbooks/precision/nddma_srcstride_0.md)（`exemplifies`）：GetStride 与《NDDMA 最内层 srcStride=0 广播读越界》的实质衔接是：GetStride 从 Layout 读取 MakeStride 生成的维度步长，Crd2Idx 以该 stride 映射坐标；NDDMA stride=0 故障和 Layout 说明验证物理寻址边界。
- [Crd2Idx](../coordinate/crd2_idx.md)（`related`）：Crd2Idx 与《GetStride》的实质衔接是：Crd2Idx 用 Coordinate 与 Layout 的 shape/stride 计算线性索引，MakeCoord、Layout/TensorDesc 构造和 GetStride 提供两种重载所需的数据结构。
- [GetShape](get_shape.md)（`related`）：GetShape 与 GetStride 分别取同一 Layout 的维度和步长，联合后才能完整解释多维内存排布。
- [GetStride](../../data_structure_tensor_api/layout_structure/get_stride.md)（`related`）：GetStride说明返回描述内存访问步长的Stride对象，与Shape的维度信息一一对应。
- [Layout数据结构](../../data_structure_tensor_api/layout_structure/layout_structure.md)（`related`）：GetStride 与《Layout数据结构》的实质衔接是：GetStride 从 Layout 读取 MakeStride 生成的维度步长，Crd2Idx 以该 stride 映射坐标；NDDMA stride=0 故障和 Layout 说明验证物理寻址边界。
- [Layout构造函数](layout_constructor.md)（`related`）：《Layout构造函数》说明根据输入的Shape和Stride对象，实例化Layout对象。；《GetStride》说明返回描述内存访问步长的Stride对象，与Shape的维度信息一一对应。。二者在Layout由Shape与Stride构造，MakeLayout、GetShape/GetStride、Crd2Idx和is_layout共同定义其类型与索引合同上存在可执行的直接衔接。
- [Layout简介](layout_intro.md)（`related`）：GetStride 读取 Layout 的地址步长，与 shape 一起决定逻辑坐标到线性地址的映射。
- [Layout（辅助数据结构）](layout.md)（`related`）：GetStride 提取每个维度的内存步长，是 Layout 从坐标计算偏移所需的另一半信息。
- [MakeLayout](make_layout.md)（`related`）：GetStride 与《MakeLayout》的实质衔接是：GetStride 从 Layout 读取 MakeStride 生成的维度步长，Crd2Idx 以该 stride 映射坐标；NDDMA stride=0 故障和 Layout 说明验证物理寻址边界。
- [MakeShape](make_shape.md)（`related`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《GetStride》说明返回描述内存访问步长的Stride对象，与Shape的维度信息一一对应。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [layout](layout1.md)（`related`）：layout 与《GetStride》的实质衔接是：Layout 同时承载 shape、stride 与 format，由 MakeLayout 构造并通过 Get/Set 访问；Crd2Idx、排布格式与 NDExtLayout 方向故障验证其寻址语义。
- [MakeStride](make_stride.md)（`same_topic`）：GetStride 与《MakeStride》的实质衔接是：GetStride 从 Layout 读取 MakeStride 生成的维度步长，Crd2Idx 以该 stride 映射坐标；NDDMA stride=0 故障和 Layout 说明验证物理寻址边界。
<!-- cannbot:related:end -->
