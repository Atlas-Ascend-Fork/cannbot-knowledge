---
type: API
title: layout
description: 获取Layout实例化对象。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Layout/layout1.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---


# Layout结构体定义

Layout结构体用于描述Tensor的数据排布，包含shape（各维度大小）、stride（各维度步长）和format（数据格式）等成员。Layout支持ND格式（连续排布）和NZ格式（分块排布）等。通过Layout可以描述Tensor在内存中的完整排布信息，用于DataCopy等操作的数据搬运。

<!-- cannbot:related:start -->
## 相关

- [noTrans extract 与 NDExtLayoutPtn 方向不匹配](../../../../../runbooks/precision/notrans_extract_ndextlayoutptn.md)（`exemplifies`）：layout 与《noTrans extract 与 NDExtLayoutPtn 方向不匹配》的实质衔接是：Layout 同时承载 shape、stride 与 format，由 MakeLayout 构造并通过 Get/Set 访问；Crd2Idx、排布格式与 NDExtLayout 方向故障验证其寻址语义。
- [数据排布格式](../../../../../guides/technical_appendix/concepts_and_terms/neural_networks_and_operators/data_layout.md)（`explains`）：layout 与《数据排布格式》的实质衔接是：Layout 同时承载 shape、stride 与 format，由 MakeLayout 构造并通过 Get/Set 访问；Crd2Idx、排布格式与 NDExtLayout 方向故障验证其寻址语义。
- [GetShape](get_shape.md)（`related`）：layout 与《GetShape》的实质衔接是：Layout 同时承载 shape、stride 与 format，由 MakeLayout 构造并通过 Get/Set 访问；Crd2Idx、排布格式与 NDExtLayout 方向故障验证其寻址语义。
- [GetStride](get_stride.md)（`related`）：layout 与《GetStride》的实质衔接是：Layout 同时承载 shape、stride 与 format，由 MakeLayout 构造并通过 Get/Set 访问；Crd2Idx、排布格式与 NDExtLayout 方向故障验证其寻址语义。
- [MakeShape](make_shape.md)（`related`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《layout》说明获取Layout实例化对象。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [MakeStride](make_stride.md)（`related`）：layout 与《MakeStride》的实质衔接是：Layout 同时承载 shape、stride 与 format，由 MakeLayout 构造并通过 Get/Set 访问；Crd2Idx、排布格式与 NDExtLayout 方向故障验证其寻址语义。
- [Crd2Idx](../coordinate/crd2_idx.md)（`same_topic`）：layout 与《Crd2Idx》的实质衔接是：Layout 同时承载 shape、stride 与 format，由 MakeLayout 构造并通过 Get/Set 访问；Crd2Idx、排布格式与 NDExtLayout 方向故障验证其寻址语义。
- [GetLayout](../tensor_trait/get_layout.md)（`same_topic`）：layout 与《GetLayout》的实质衔接是：Layout 同时承载 shape、stride 与 format，由 MakeLayout 构造并通过 Get/Set 访问；Crd2Idx、排布格式与 NDExtLayout 方向故障验证其寻址语义。
- [Layout构造函数](layout_constructor.md)（`same_topic`）：《Layout构造函数》说明根据输入的Shape和Stride对象，实例化Layout对象。；《layout》说明获取Layout实例化对象。。二者在Layout由Shape与Stride构造，MakeLayout、GetShape/GetStride、Crd2Idx和is_layout共同定义其类型与索引合同上存在可执行的直接衔接。
- [Layout简介](layout_intro.md)（`same_topic`）：layout 与《Layout简介》的实质衔接是：Layout 同时承载 shape、stride 与 format，由 MakeLayout 构造并通过 Get/Set 访问；Crd2Idx、排布格式与 NDExtLayout 方向故障验证其寻址语义。
- [MakeLayout](make_layout.md)（`same_topic`）：layout 与《MakeLayout》的实质衔接是：Layout 同时承载 shape、stride 与 format，由 MakeLayout 构造并通过 Get/Set 访问；Crd2Idx、排布格式与 NDExtLayout 方向故障验证其寻址语义。
- [SetLayout](../tensor_trait/set_layout.md)（`same_topic`）：layout 与《SetLayout》的实质衔接是：Layout 同时承载 shape、stride 与 format，由 MakeLayout 构造并通过 Get/Set 访问；Crd2Idx、排布格式与 NDExtLayout 方向故障验证其寻址语义。
- [is_layout](is_layout.md)（`same_topic`）：《is_layout》说明判断输入的数据结构是否为Layout数据结构，可通过检查其成员常量value的值来判断。当value为true时，表示输入的数据结构是Layout类型；反之则为非Layout类型。；《layout》说明获取Layout实例化对象。。二者在is_layout用于识别Layout类型，构造、Shape/Stride访问和MakeLayout是其直接类型契约上存在可执行的直接衔接。
<!-- cannbot:related:end -->
