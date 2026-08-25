---
type: API
title: GetShape
description: 返回描述张量形状的Shape对象。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Layout/GetShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# GetShape

获取Layout的Shape信息。返回Layout中描述的各维度大小。函数原型：Shape GetShape() const。返回Shape结构体，包含各维度大小。用于查询Tensor的形状信息。

<!-- cannbot:related:start -->
## 相关

- [GetStride](get_stride.md)（`related`）：GetShape 与 GetStride 分别取同一 Layout 的维度和步长，联合后才能完整解释多维内存排布。
- [Layout构造函数](layout_constructor.md)（`related`）：《Layout构造函数》说明根据输入的Shape和Stride对象，实例化Layout对象。；《GetShape》说明返回描述张量形状的Shape对象。。二者在Layout由Shape与Stride构造，MakeLayout、GetShape/GetStride、Crd2Idx和is_layout共同定义其类型与索引合同上存在可执行的直接衔接。
- [Layout（辅助数据结构）](layout.md)（`related`）：GetShape 提取 Layout 的逻辑维度，与 GetStride 联合才能完整解释布局。
- [MakeShape](make_shape.md)（`related`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《GetShape》说明返回描述张量形状的Shape对象。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [layout](layout1.md)（`related`）：layout 与《GetShape》的实质衔接是：Layout 同时承载 shape、stride 与 format，由 MakeLayout 构造并通过 Get/Set 访问；Crd2Idx、排布格式与 NDExtLayout 方向故障验证其寻址语义。
- [Layout简介](layout_intro.md)（`same_topic`）：Layout 由 Shape 与 Stride 共同描述逻辑维度到内存地址映射，GetShape 提取其中的逻辑维度部分。
<!-- cannbot:related:end -->
