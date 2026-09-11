---
type: API
title: Output（OpDef）
description: 注册算子输出，调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输出信息。
tags:
- task.lookup
- topic.implementation.api_layer.utils_api
- topic.implementation.operator_registration
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpDef/Output.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms: []
---

# Output<a name="ZH-CN_TOPIC_0000002078492688"></a>

## 功能说明<a name="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_section36583473819"></a>

注册算子输出，调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输出信息。

## 函数原型<a name="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_section13230182415108"></a>

```
OpParamDef &Output(const char *name)
```

## 参数说明<a name="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_section75395119104"></a>

<a name="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_table111938719446"></a>
<table><thead align="left"><tr id="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_row6223476444"><th class="cellrowborder" valign="top" width="17.22%" id="mcps1.1.4.1.1"><p id="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_p10223674448"><a name="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_p10223674448"></a><a name="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_p10223674448"></a>参数</p>
</th>
<th class="cellrowborder" valign="top" width="15.340000000000002%" id="mcps1.1.4.1.2"><p id="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_p645511218169"><a name="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_p645511218169"></a><a name="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_p645511218169"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="67.44%" id="mcps1.1.4.1.3"><p id="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_p1922337124411"><a name="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_p1922337124411"></a><a name="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_p1922337124411"></a>说明</p>
</th>
</tr>
</thead>
<tbody><tr id="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_row152234713443"><td class="cellrowborder" valign="top" width="17.22%" headers="mcps1.1.4.1.1 "><p id="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_p318615392613"><a name="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_p318615392613"></a><a name="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_p318615392613"></a>name</p>
</td>
<td class="cellrowborder" valign="top" width="15.340000000000002%" headers="mcps1.1.4.1.2 "><p id="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_p320343694214"><a name="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_p320343694214"></a><a name="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_p320343694214"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="67.44%" headers="mcps1.1.4.1.3 "><p id="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_p453018873120"><a name="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_p453018873120"></a><a name="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_p453018873120"></a>算子输出名称。</p>
</td>
</tr>
</tbody>
</table>

## 返回值说明<a name="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_section25791320141317"></a>

算子参数定义，OpParamDef实例，具体请参考[OpParamDef](../op_param_def/index.md)。

## 约束说明<a name="zh-cn_topic_0000001549347676_zh-cn_topic_0000001576870901_zh-cn_topic_0000001575944081_section19165124931511"></a>

参数注册的顺序需要和算子kernel入口函数一致。



<!-- cannbot:related:start -->
## 相关

- [advance_step in-place kernel FATBIN wrap](../../../../runbooks/compilation/fatbin_wrapper_param_count_matches_opdef_input_plus_output.md)（`exemplifies`）：ascend950 FATBIN 阶段为 kernel 自动生成一个 wrapper，wrapper 的调用实参数 = `OpDef` 声明的 input 数 + output 数 + workspace + tiling。；参数注册的顺序需要和算子kernel入口函数一致。；Output API 规定注册顺序与 Kernel 入口一致，排障实例进一步证明 wrapper 会按 input、output、workspace、tiling 机械生成实参，因此 Kernel 签名必须同时对齐 Output 数量和顺序。
<!-- cannbot:related:end -->
