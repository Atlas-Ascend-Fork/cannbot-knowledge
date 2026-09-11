---
type: API
title: Format（OpParamDef）
description: 定义算子参数数据格式。
tags:
- task.lookup
- topic.implementation.api_layer.utils_api
- topic.implementation.operator_registration
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/Format.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms: []
---

# Format<a name="ZH-CN_TOPIC_0000002114097057"></a>

## 功能说明<a name="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_zh-cn_topic_0000001525424352_section36583473819"></a>

定义算子参数数据格式。

## 函数原型<a name="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_zh-cn_topic_0000001525424352_section13230182415108"></a>

```
OpParamDef &Format(std::vector<ge::Format> formats)
```

## 参数说明<a name="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_zh-cn_topic_0000001525424352_section75395119104"></a>

<a name="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_zh-cn_topic_0000001575944081_table111938719446"></a>
<table><thead align="left"><tr id="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_zh-cn_topic_0000001575944081_row6223476444"><th class="cellrowborder" valign="top" width="17.22%" id="mcps1.1.4.1.1"><p id="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_zh-cn_topic_0000001575944081_p10223674448"><a name="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_zh-cn_topic_0000001575944081_p10223674448"></a><a name="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_zh-cn_topic_0000001575944081_p10223674448"></a>参数</p>
</th>
<th class="cellrowborder" valign="top" width="15.340000000000002%" id="mcps1.1.4.1.2"><p id="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_zh-cn_topic_0000001575944081_p645511218169"><a name="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_zh-cn_topic_0000001575944081_p645511218169"></a><a name="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_zh-cn_topic_0000001575944081_p645511218169"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="67.44%" id="mcps1.1.4.1.3"><p id="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_zh-cn_topic_0000001575944081_p1922337124411"><a name="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_zh-cn_topic_0000001575944081_p1922337124411"></a><a name="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_zh-cn_topic_0000001575944081_p1922337124411"></a>说明</p>
</th>
</tr>
</thead>
<tbody><tr id="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_zh-cn_topic_0000001575944081_row152234713443"><td class="cellrowborder" valign="top" width="17.22%" headers="mcps1.1.4.1.1 "><p id="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_zh-cn_topic_0000001575944081_p318615392613"><a name="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_zh-cn_topic_0000001575944081_p318615392613"></a><a name="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_zh-cn_topic_0000001575944081_p318615392613"></a>formats</p>
</td>
<td class="cellrowborder" valign="top" width="15.340000000000002%" headers="mcps1.1.4.1.2 "><p id="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_zh-cn_topic_0000001575944081_p320343694214"><a name="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_zh-cn_topic_0000001575944081_p320343694214"></a><a name="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_zh-cn_topic_0000001575944081_p320343694214"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="67.44%" headers="mcps1.1.4.1.3 "><p id="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_p43231148103313"><a name="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_p43231148103313"></a><a name="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_p43231148103313"></a>算子参数数据格式。</p>
</td>
</tr>
</tbody>
</table>

## 返回值说明<a name="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_zh-cn_topic_0000001525424352_section25791320141317"></a>

OpParamDef算子定义，OpParamDef请参考[OpParamDef](index.md)。

## 约束说明<a name="zh-cn_topic_0000001549188228_zh-cn_topic_0000001526275046_zh-cn_topic_0000001525424352_section19165124931511"></a>

无



<!-- cannbot:related:start -->
## 相关

- [OpDef FORMAT_NCHW 致 5D 报 161002](../../../../runbooks/compilation/opdef_format_nchw_5d_161002.md)（`exemplifies`）：“CANN 的 `ACL_FORMAT_NCHW` 仅对 4D 张量有效；5D 张量（`［N,D,C,H,W］`）没有 NCHW 这一物理格式，OpDef 强制 NCHW 会让 5D 输入在 `GetWorkspaceSize` 阶段被拒。”与“定义算子参数数据格式。”提供双方正文证据。Format API 给出 OpDef 参数格式定义入口，运行手册具体证明把 5D 输入定义为 NCHW 会在 GetWorkspaceSize 返回 161002，并给出保持 FORMAT_ND、由 shape 推断布局的边界。
- [UnknownShapeFormat](unknown_shape_format_deprecated.md)（`same_topic`）：该接口废弃，并将在后续版本移除，请不要使用该接口。无需针对动态/静态shape单独设置format，统一使用Format接口来设置即可。定义算子参数数据格式。废弃卡明确把 UnknownShapeFormat 的职责迁移到 Format，目标卡定义承接后的参数格式设置合同；替换后还能消除 deprecated 警告在严格编译选项下升级为错误的风险。
<!-- cannbot:related:end -->
