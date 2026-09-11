---
type: API
title: GET_TILING_DATA
description: 用于获取算子kernel入口函数传入的Tiling信息，并填入注册的TilingData结构体中，此函数会以宏展开的方式进行编译。对应的算子host实现中需要定义TilingData结构体，实现并注册计算TilingData的Tiling函数。如果用户通过TilingData结构注册注册了多个TilingData结构体，使用该接口返回默认注册的结构体。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.tiling
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/GET_TILING_DATA.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
---

# GET\_TILING\_DATA<a name="ZH-CN_TOPIC_0000001637034733"></a>

## 功能说明<a name="zh-cn_topic_0000001526206862_section212607105720"></a>

用于获取算子kernel入口函数传入的Tiling信息，并填入注册的TilingData结构体中，此函数会以宏展开的方式进行编译。对应的算子host实现中需要定义TilingData结构体，实现并注册计算TilingData的Tiling函数。如果用户通过[TilingData结构注册](../../../utils_api/tiling_data_structure_register/tiling_data_struct_register.md)注册了多个TilingData结构体，使用该接口返回默认注册的结构体。

## 函数原型<a name="zh-cn_topic_0000001526206862_section1630753514297"></a>

```
GET_TILING_DATA(tiling_data, tiling_arg)
```

## 参数说明<a name="zh-cn_topic_0000001526206862_section129451113125413"></a>

<a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_table111938719446"></a>
<table><thead align="left"><tr id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_row6223476444"><th class="cellrowborder" valign="top" width="17.22%" id="mcps1.1.4.1.1"><p id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p10223674448"><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p10223674448"></a><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p10223674448"></a>参数</p>
</th>
<th class="cellrowborder" valign="top" width="15.340000000000002%" id="mcps1.1.4.1.2"><p id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p645511218169"><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p645511218169"></a><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p645511218169"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="67.44%" id="mcps1.1.4.1.3"><p id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p1922337124411"><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p1922337124411"></a><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p1922337124411"></a>说明</p>
</th>
</tr>
</thead>
<tbody><tr id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_row152234713443"><td class="cellrowborder" valign="top" width="17.22%" headers="mcps1.1.4.1.1 "><p id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p2340183613156"><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p2340183613156"></a><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p2340183613156"></a>tiling_data</p>
</td>
<td class="cellrowborder" valign="top" width="15.340000000000002%" headers="mcps1.1.4.1.2 "><p id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p320343694214"><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p320343694214"></a><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p320343694214"></a>输出</p>
</td>
<td class="cellrowborder" valign="top" width="67.44%" headers="mcps1.1.4.1.3 "><p id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p2684123934216"><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p2684123934216"></a><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p2684123934216"></a>返回默认TilingData结构体变量。</p>
</td>
</tr>
<tr id="zh-cn_topic_0000001526206862_row1239183183016"><td class="cellrowborder" valign="top" width="17.22%" headers="mcps1.1.4.1.1 "><p id="zh-cn_topic_0000001526206862_p223953193015"><a name="zh-cn_topic_0000001526206862_p223953193015"></a><a name="zh-cn_topic_0000001526206862_p223953193015"></a>tiling_arg</p>
</td>
<td class="cellrowborder" valign="top" width="15.340000000000002%" headers="mcps1.1.4.1.2 "><p id="zh-cn_topic_0000001526206862_p7239938308"><a name="zh-cn_topic_0000001526206862_p7239938308"></a><a name="zh-cn_topic_0000001526206862_p7239938308"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="67.44%" headers="mcps1.1.4.1.3 "><p id="zh-cn_topic_0000001526206862_p72396320307"><a name="zh-cn_topic_0000001526206862_p72396320307"></a><a name="zh-cn_topic_0000001526206862_p72396320307"></a>此参数为算子入口函数处传入的Tiling参数。</p>
</td>
</tr>
</tbody>
</table>

## 约束说明<a name="zh-cn_topic_0000001526206862_section65498832"></a>

-   本函数需在算子kernel代码处使用，并且传入的tiling\_data参数不需要声明类型。
-   暂不支持kernel直调工程。

## 调用示例<a name="zh-cn_topic_0000001526206862_section97001499599"></a>

```
extern "C" __global__ __aicore__ void add_custom(__gm__ uint8_t *x, __gm__ uint8_t *y, __gm__ uint8_t *z, __gm__ uint8_t *tiling)
{
    GET_TILING_DATA(tilingData, tiling);// 反序列化SaveToBuffer生成的数据，并填入注册的TilingData结构体中
    KernelAdd op;
    op.Init(x, y, z, tilingData.numBlocks, tilingData.totalSize, tilingData.splitTile);
    op.Process();
}
```

配套的host侧Tiling函数示例：

```
ge::graphStatus TilingFunc(gert::TilingContext* context)
{
    // 其他代码逻辑
    ...
    TilingData tiling;  // 与算子host实现中定义TilingData结构体的对应
    tiling.set_blkDim(numBlocks);  // 与算子host实现中定义TilingData结构体中的成员的对应
    tiling.set_totalSize(totalSize);
    tiling.set_splitTile(splitTile);
    tiling.SaveToBuffer(context->GetRawTilingData()->GetData(), context->GetRawTilingData()->GetCapacity());
    ...
    // 其他代码逻辑
}
```


<!-- cannbot:related:start -->
## 相关

- [ACLNN 507035 — stub kernel tiling 数据未初始化](../../../../runbooks/compilation/aclnn_507035_stub_tilingfunc_must_init_tiling_buffer.md)（`exemplifies`）：stub TilingFunc 必须调用 `context->GetTilingData<TilingDataT>()` 取得指针并写入至少一个字段（如 `totalLength`），再 `SetBlockDim`/workspace；kernel 侧保持接口桩不变。修复后 11/11 冒烟通过。；获取算子 kernel 入口函数传入的 Tiling 信息，填入注册的 TilingData 结构体。以宏展开方式编译。Host 侧需定义 TilingData 结构体并注册 Tiling 函数。返回默认注册的结构体。支持 950/a2/a3。。运行手册用 Host GetTilingData 初始化字段来消除 stub 的 507035，API 卡说明 Kernel 宏如何读取注册结构体，二者把故障修复连接到 Host 生产、Device 消费同一 TilingData 缓冲的合同。
- [GET_TILING_DATA 首参传类型名致变量遮蔽类型](../../../../runbooks/compilation/get_tiling_data.md)（`exemplifies`）：获取算子 kernel 入口函数传入的 Tiling 信息，填入注册的 TilingData 结构体。以宏展开方式编译。Host 侧需定义 TilingData 结构体并注册 Tiling 函数。返回默认注册的结构体。支持 950/a2/a3。；`GET_TILING_DATA(var_name, tiling_arg)` → 展开为 `HistogramTilingData var_name; InitTilingData<HistogramTilingData>(tiling_arg, &var_name);`（首参为变量名，非类型名）。。运行手册用真实宏展开说明接口首参为何必须是变量名，并给出编译失败探针。
- [TilingData 须 host 与 kernel 各定义一份](../../../../runbooks/compilation/tilingdata_host_kernel.md)（`exemplifies`）：AscendC 算子的 TilingData struct 需要同时被两个编译器看到：；获取算子 kernel 入口函数传入的 Tiling 信息，填入注册的 TilingData 结构体。以宏展开方式编译。Host 侧需定义 TilingData 结构体并注册 Tiling 函数。返回默认注册的结构体。支持 950/a2/a3。runbook 的 host 完整类型报错发生在生产侧，GET_TILING_DATA 页明确 Kernel 消费同一注册结构体，能核对两端 ABI。
- [限制TilingData结构大小](../../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/limit_tiling_data_size.md)（`explains`）：“调用GET_TILING_DATA宏后，会将Tiling信息从GM拷贝到AI处理器的栈空间上，期间会有拷贝开销，由于GM访问效率较低，同时考虑到栈空间限制，需要限制TilingData结构大小。”；“获取算子 kernel 入口函数传入的 Tiling 信息，填入注册的 TilingData 结构体。以宏展开方式编译。”。Guide 解释为何要减小 GET_TILING_DATA 从 GM 到栈的搬运量，API 卡界定该宏的实际取数行为。
- [DequantBias A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/quant/dequant_bias.md)（`related`）：“Host `SaveToBuffer` 与 Device `GET_TILING_DATA` 使用同一注册结构，字段顺序不得改变。”给出 DequantBias 的 POD ABI 闭环；“获取算子 kernel 入口函数传入的 Tiling 信息，填入注册的 TilingData 结构体。”说明 Device 宏在该闭环中的消费职责。
- [HardswishBackwardV2 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/hardswish_backward_v2_950.md)（`related`）：“GET_TILING_DATA(tilingData, tiling);”；“获取算子 kernel 入口函数传入的 Tiling 信息，填入注册的 TilingData 结构体。以宏展开方式编译。”。950 operator entry 实际调用该宏把 Host 生成的 HardSwishGradV2TilingData 解析到 Device，API 定义其宏展开合同。
- [TilingData结构定义](../../../utils_api/tiling_data_structure_register/tiling_data_struct_definition.md)（`related`）：“- SaveToBuffer接口：完成TilingData的序列化和保存。”；“获取算子 kernel 入口函数传入的 Tiling 信息，填入注册的 TilingData 结构体。”。Host 序列化的 TilingData 经 kernel 入参传递后由 GET_TILING_DATA 反序列化到同一注册结构。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 173 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Im2colBackward 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/im2col_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA(...)` 的直接调用（第 33 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/col2im/op_kernel/col2im.cpp#L33)
- [CircularPad2d A2/A3 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/circular_pad_2d.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA(...)` 的直接调用（第 22 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/circular_pad/op_kernel/circular_pad.cpp#L22)
- [FatreluMul A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/fatrelu_mul.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA(...)` 的直接调用（第 25 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/fatrelu_mul/op_kernel/fatrelu_mul.cpp#L25)
- [ChunkGatedDeltaRule A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/chunk_gated_delta_rule.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA(...)` 的直接调用（第 28 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/chunk_gated_delta_rule/op_kernel/chunk_gated_delta_rule.cpp#L28)
- [Resize 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/resize_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA(...)` 的直接调用（第 46 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bilinear_v2/op_kernel/resize_bilinear_v2_apt.cpp#L46)
- [CircularPad2dBackward A2/A3 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/circular_pad_2d_backward.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA(...)` 的直接调用（第 22 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/circular_pad_grad/op_kernel/circular_pad_grad.cpp#L22)
- [GeGluBackward A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/ge_glu_backward.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA(...)` 的直接调用（第 41 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/ge_glu_grad_v2/op_kernel/ge_glu_grad_v2.cpp#L41)
- [NsaCompressAttentionInfer A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/nsa_compress_attention_infer.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA(...)` 的直接调用（第 33 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/nsa_compress_attention_infer/op_kernel/nsa_compress_attention_infer.cpp#L33)
- [ThreeInterpolateBackward A2/A3 ACLNN 算子知识](../../../../operators/aclnn/cv/image/three_interpolate_backward.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA(...)` 的直接调用（第 351 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/three_interpolate_backward/op_kernel/three_interpolate_backward.cpp#L351)
- [CircularPad3d A2/A3 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/circular_pad_3d.md)（`related`）：算子声明的固定版本源码包含对 `GET_TILING_DATA(...)` 的直接调用（第 22 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/circular_pad/op_kernel/circular_pad.cpp#L22)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
