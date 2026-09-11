---
type: API
title: SetInferShape
description: 使用图模式时，需要调用该接口注册Shape推导函数。
tags:
- task.lookup
- topic.implementation.api_layer.utils_api
- topic.implementation.operator_registration
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpDef/SetInferShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms: []
---

# SetInferShape<a name="ZH-CN_TOPIC_0000002114052021"></a>

## 功能说明<a name="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_zh-cn_topic_0000001525424352_section36583473819"></a>

使用图模式时，需要调用该接口注册Shape推导函数。

## 函数原型<a name="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_zh-cn_topic_0000001525424352_section13230182415108"></a>

```
OpDef &SetInferShape(gert::OpImplRegisterV2::InferShapeKernelFunc func)
```

## 参数说明<a name="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_zh-cn_topic_0000001525424352_section75395119104"></a>

<a name="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_zh-cn_topic_0000001575944081_table111938719446"></a>
<table><thead align="left"><tr id="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_zh-cn_topic_0000001575944081_row6223476444"><th class="cellrowborder" valign="top" width="17.22%" id="mcps1.1.4.1.1"><p id="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_zh-cn_topic_0000001575944081_p10223674448"><a name="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_zh-cn_topic_0000001575944081_p10223674448"></a><a name="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_zh-cn_topic_0000001575944081_p10223674448"></a>参数</p>
</th>
<th class="cellrowborder" valign="top" width="15.340000000000002%" id="mcps1.1.4.1.2"><p id="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_zh-cn_topic_0000001575944081_p645511218169"><a name="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_zh-cn_topic_0000001575944081_p645511218169"></a><a name="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_zh-cn_topic_0000001575944081_p645511218169"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="67.44%" id="mcps1.1.4.1.3"><p id="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_zh-cn_topic_0000001575944081_p1922337124411"><a name="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_zh-cn_topic_0000001575944081_p1922337124411"></a><a name="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_zh-cn_topic_0000001575944081_p1922337124411"></a>说明</p>
</th>
</tr>
</thead>
<tbody><tr id="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_zh-cn_topic_0000001575944081_row152234713443"><td class="cellrowborder" valign="top" width="17.22%" headers="mcps1.1.4.1.1 "><p id="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_zh-cn_topic_0000001575944081_p318615392613"><a name="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_zh-cn_topic_0000001575944081_p318615392613"></a><a name="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_zh-cn_topic_0000001575944081_p318615392613"></a>func</p>
</td>
<td class="cellrowborder" valign="top" width="15.340000000000002%" headers="mcps1.1.4.1.2 "><p id="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_zh-cn_topic_0000001575944081_p320343694214"><a name="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_zh-cn_topic_0000001575944081_p320343694214"></a><a name="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_zh-cn_topic_0000001575944081_p320343694214"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="67.44%" headers="mcps1.1.4.1.3 "><p id="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_p096733515614"><a name="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_p096733515614"></a><a name="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_p096733515614"></a>Shape推导函数。InferShapeKernelFunc类型定义如下：</p>
<a name="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_screen17603182541315"></a><a name="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_screen17603182541315"></a><pre class="screen" codetype="Cpp" id="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_screen17603182541315">using InferShapeKernelFunc = UINT32 (*)(InferShapeContext *);</pre>
</td>
</tr>
</tbody>
</table>

## 返回值说明<a name="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_zh-cn_topic_0000001525424352_section25791320141317"></a>

OpDef算子定义，OpDef请参考[OpDef](index.md)。

## 约束说明<a name="zh-cn_topic_0000001600267337_zh-cn_topic_0000001526112350_zh-cn_topic_0000001525424352_section19165124931511"></a>

无



<!-- cannbot:related:start -->
## 相关

- [InferShape 返回 identity 致空 kernel 假通过](../../../../runbooks/precision/infershape_identity_kernel.md)（`exemplifies`）：“`InferShape` 必须按算子真实语义计算输出 shape，不可长期保留 `*output=*input` stub；调试"空 kernel 却有通过"时第一探针即查 InferShape 是否返回 identity。”记录注册回调若长期保留 identity stub 会让形状变换算子假通过；“使用图模式时，需要调用该接口注册Shape推导函数。”定义 SetInferShape 是图模式挂载该回调的入口。该边把假通过诊断落到需要检查的注册函数。
- [缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape](../../../../runbooks/compilation/op_proto_lib_axes_infershape.md)（`exemplifies`）：“**`cust_proto_obj` 未定义 `OP_PROTO_LIB`**：标准 CANN 模板（`npu_op_library` GRAPH 编译源时）会给 proto 目标加 `OP_PROTO_LIB`，使 `OP_ADD` 经 `OpImplRegisterV2` 把 OpDef 上 `SetInferShape`/`SetInferDataType` 注册的 gert V2 InferShape 注入 rt2 registry。”与“使用图模式时，需要调用该接口注册Shape推导函数。”提供双方正文证据。API 卡给出图模式必须注册 Shape 推导函数的合同，运行手册展示即使调用 SetInferShape，若 proto 目标缺 OP_PROTO_LIB，注册也不会注入 rt2 registry 并会回落到 built-in InferShape。
- [SetInferDataType](set_infer_data_type.md)（`same_topic`）：使用图模式时，需要调用该接口注册DataType推导函数。 使用图模式时，需要调用该接口注册Shape推导函数。 图模式 OpDef 分别需要 dtype 和 shape 推导注册，两接口共同闭合输出元数据推导。
<!-- cannbot:related:end -->
