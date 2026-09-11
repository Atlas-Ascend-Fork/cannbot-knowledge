---
type: API
title: GET_TPL_TILING_KEY
description: Tiling模板编程时，开发者通过调用此接口自动生成TilingKey。该接口将传入的模板参数通过定义的位宽，转成二进制，按照顺序组合后转成uint64数值，即TilingKey。
  使用该接口需要包含定义模板参数和模板参数组合的头文件。详细内容请参考Tiling模板编程。
tags:
- task.lookup
- topic.implementation.api_layer.utils_api
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_template_programming/GET_TPL_TILING_KEY.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms: []
source_headers:
- include/utils/tiling/template_argument.h
---

# GET\_TPL\_TILING\_KEY<a name="ZH-CN_TOPIC_0000002103405630"></a>

## 功能说明<a name="zh-cn_topic_0000001867289945_zh-cn_topic_0000001389787297_section36583473819"></a>

Tiling模板编程时，开发者通过调用此接口自动生成TilingKey。该接口将传入的模板参数通过定义的位宽，转成二进制，按照顺序组合后转成uint64数值，即TilingKey。

使用该接口需要包含定义模板参数和模板参数组合的头文件。详细内容请参考[Tiling模板编程](index.md)。

## 函数原型<a name="zh-cn_topic_0000001867289945_zh-cn_topic_0000001389787297_section13230182415108"></a>

```
namespace AscendC {
    uint64_t EncodeTilingKey(TilingDeclareParams declareParams,
                             TilingSelectParams selectParamsVec,
                             std::vector<uint64_t> tilingParams);
}

#define GET_TPL_TILING_KEY(...) \
    AscendC::EncodeTilingKey(g_tilingDeclareParams, g_tilingSelectParams, {__VA_ARGS__}) // GET_TPL_TILING_KEY通过调用EncodeTilingKey接口生成TilingKey， EncodeTilingKey属于内部关联接口，开发者无需关注
```

## 参数说明<a name="zh-cn_topic_0000001867289945_zh-cn_topic_0000001389787297_section75395119104"></a>

<a name="zh-cn_topic_0000001820490272_zh-cn_topic_0000001389787297_table111938719446"></a>
<table><thead align="left"><tr id="zh-cn_topic_0000001820490272_zh-cn_topic_0000001389787297_row6223476444"><th class="cellrowborder" valign="top" width="17.22%" id="mcps1.1.4.1.1"><p id="zh-cn_topic_0000001820490272_zh-cn_topic_0000001389787297_p10223674448"><a name="zh-cn_topic_0000001820490272_zh-cn_topic_0000001389787297_p10223674448"></a><a name="zh-cn_topic_0000001820490272_zh-cn_topic_0000001389787297_p10223674448"></a>参数</p>
</th>
<th class="cellrowborder" valign="top" width="15.340000000000002%" id="mcps1.1.4.1.2"><p id="zh-cn_topic_0000001820490272_zh-cn_topic_0000001389787297_p645511218169"><a name="zh-cn_topic_0000001820490272_zh-cn_topic_0000001389787297_p645511218169"></a><a name="zh-cn_topic_0000001820490272_zh-cn_topic_0000001389787297_p645511218169"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="67.44%" id="mcps1.1.4.1.3"><p id="zh-cn_topic_0000001820490272_zh-cn_topic_0000001389787297_p1922337124411"><a name="zh-cn_topic_0000001820490272_zh-cn_topic_0000001389787297_p1922337124411"></a><a name="zh-cn_topic_0000001820490272_zh-cn_topic_0000001389787297_p1922337124411"></a>说明</p>
</th>
</tr>
</thead>
<tbody><tr id="zh-cn_topic_0000001820490272_zh-cn_topic_0000001389787297_row152234713443"><td class="cellrowborder" valign="top" width="17.22%" headers="mcps1.1.4.1.1 "><p id="p1693913355118"><a name="p1693913355118"></a><a name="p1693913355118"></a>...</p>
</td>
<td class="cellrowborder" valign="top" width="15.340000000000002%" headers="mcps1.1.4.1.2 "><p id="zh-cn_topic_0000001820490272_zh-cn_topic_0000001389787297_p15663137127"><a name="zh-cn_topic_0000001820490272_zh-cn_topic_0000001389787297_p15663137127"></a><a name="zh-cn_topic_0000001820490272_zh-cn_topic_0000001389787297_p15663137127"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="67.44%" headers="mcps1.1.4.1.3 "><p id="p010373710272"><a name="p010373710272"></a><a name="p010373710272"></a>可变长参数，模板参数的具体值，传入时需要与定义模板参数和模板参数组合的头文件中的模板参数顺序保持一致。</p>
</td>
</tr>
</tbody>
</table>

## 返回值说明<a name="zh-cn_topic_0000001867289945_zh-cn_topic_0000001389787297_section25791320141317"></a>

TilingKey数值。

## 约束说明<a name="zh-cn_topic_0000001867289945_zh-cn_topic_0000001389787297_section19165124931511"></a>

无。

## 调用示例<a name="zh-cn_topic_0000001867289945_zh-cn_topic_0000001389787297_section320753512363"></a>

```
#include "tiling_key_add_custom.h"
static ge::graphStatus TilingFunc(gert::TilingContext *context)
{
    TilingDataTemplate tiling;
    uint32_t totalLength = context->GetInputShape(0)->GetOriginShape().GetShapeSize();
    ge::DataType dtype_x = context->GetInputDesc(0)->GetDataType();
    ge::DataType dtype_y = context->GetInputDesc(1)->GetDataType();
    ge::DataType dtype_z = context->GetOutputDesc(0)->GetDataType();
    uint32_t D_T_X = static_cast<int>(dtype_x), D_T_Y = static_cast<int>(dtype_y), D_T_Z = static_cast<int>(dtype_z), TILE_NUM = 1, IS_SPLIT = 0;
    if (totalLength < MIN_LENGTH_FOR_SPLIT) {
        IS_SPLIT = 0;
        TILE_NUM = 1;
    } else {
        IS_SPLIT = 1;
        TILE_NUM = DEFAULT_TILE_NUM;
    }
    context->SetSimdNumBlocks(NUM_BLOCKS);
    tiling.set_totalLength(totalLength);
    tiling.SaveToBuffer(context->GetRawTilingData()->GetData(), context->GetRawTilingData()->GetCapacity());
    context->GetRawTilingData()->SetDataSize(tiling.GetDataSize());
    const uint64_t tilingKey = GET_TPL_TILING_KEY(D_T_X, D_T_Y, D_T_Z, TILE_NUM, IS_SPLIT);  // 模板参数tilingkey配置
    context->SetTilingKey(tilingKey);
    size_t *currentWorkspace = context->GetWorkspaceSizes(1);
    currentWorkspace[0] = 0;
    return ge::GRAPH_SUCCESS;
}
```



<!-- cannbot:related:start -->
## 相关

- [sub-kernel 后缀 _N 是 tilingKey 位编码非序号](../../../runbooks/compilation/sub_kernel_n_tilingkey.md)（`exemplifies`）：**API 路径**: `GET_TPL_TILING_KEY(...)` 宏 → `AscendC::FastEncodeTilingKeyDirect(g_tilingDeclareParams, {...})`（`tiling/template_argument.h:291-325`）；Tiling模板编程时，开发者通过调用此接口自动生成TilingKey。该接口将传入的模板参数通过定义的位宽，转成二进制，按照顺序组合后转成uint64数值，即TilingKey。。该 runbook 通过 sub-kernel 后缀实证 GET_TPL_TILING_KEY 的位宽顺序编码结果，说明后缀是编码值而非连续序号。
- [tilingKey 编码与 TPL 位打包不一致致路由错误](../../../runbooks/compilation/tiling_key_tpl_bit_encoding_mismatch.md)（`exemplifies`）：焦点 runbook 的修复结论是“host tilingKey 必须等于 TPL 位编码值”，候选 API 定义“该接口将传入的模板参数通过定义的位宽，转成二进制，按照顺序组合后转成uint64数值，即TilingKey。”；API 的位宽顺序正是重算 Host key、避免路由错模板的权威合同。
- [模板参数定义](template_params_definition.md)（`related`）：“使用该接口需要包含定义模板参数和模板参数组合的头文件。详细内容请参考Tiling模板编程。”与“通过以下函数原型进行模板参数ASCENDC_TPL_ARGS_DECL和模板参数组合ASCENDC_TPL_ARGS_SEL（即可使用的模板）的定义。详细内容请参考Tiling模板编程。”提供双方正文证据。GET_TPL_TILING_KEY 明确依赖模板参数和组合定义，另一卡给出 ASCENDC_TPL_ARGS_DECL/SEL 这两个定义入口，形成定义后再编码 TilingKey 的顺序。
- [ASCENDC_TPL_SEL_PARAM](ascendc_tpl_sel_param.md)（`same_topic`）：“宏展开后调用 GET_TPL_TILING_KEY 计算模板参数对应的 key 值，再通过 context->SetTilingKey 设置。”；“该接口将传入的模板参数通过定义的位宽，转成二进制，按照顺序组合后转成uint64数值，即TilingKey。”。目标接口定义焦点宏内部生成 key 的编码步骤。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 78 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [CircularPad2dBackward 950 ACLNN 算子知识](../../../operators/aclnn/math/conversion/circular_pad_2d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TPL_TILING_KEY(...)` 的直接调用（第 892 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3_grad/op_host/arch35/pad_v3_grad_tiling_arch35.cpp#L892)
- [Prelu 950 ACLNN 算子知识](../../../operators/aclnn/nn/activation/prelu_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TPL_TILING_KEY(...)` 的直接调用（第 97 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/p_relu/op_host/arch35/p_relu_tiling_arch35.cpp#L97)
- [FlashAttentionScore 950 ACLNN 算子知识](../../../operators/aclnn/transformer/attention/flash_attention_score_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TPL_TILING_KEY(...)` 的直接调用（第 306 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attention_score/op_host/flash_attention_score_tiling.cpp#L306)
- [ReflectionPad2dBackward 950 ACLNN 算子知识](../../../operators/aclnn/math/conversion/reflection_pad_2d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TPL_TILING_KEY(...)` 的直接调用（第 892 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3_grad/op_host/arch35/pad_v3_grad_tiling_arch35.cpp#L892)
- [Threshold 950 ACLNN 算子知识](../../../operators/aclnn/nn/activation/threshold_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TPL_TILING_KEY(...)` 的直接调用（第 177 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/threshold_v2/op_host/arch35/threshold_v2_tiling_arch35.cpp#L177)
- [FlashAttentionScoreGrad A2/A3 ACLNN 算子知识](../../../operators/aclnn/transformer/attention/flash_attention_score_grad.md)（`related`）：算子声明的固定版本源码包含对 `GET_TPL_TILING_KEY(...)` 的直接调用（第 159 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attention_score_grad/op_host/arch22/flash_attention_score_grad_tiling_bngs1s2_b.cpp#L159)
- [Atan2 950 ACLNN 算子知识](../../../operators/aclnn/math/math/atan2_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TPL_TILING_KEY(...)` 的直接调用（第 80 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/atan2/op_host/arch35/atan2_tiling_arch35.cpp#L80)
- [ForeachAsin 950 ACLNN 算子知识](../../../operators/aclnn/nn/foreach/foreach_asin_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TPL_TILING_KEY(...)` 的直接调用（第 118 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_asin/op_host/arch35/foreach_asin_tiling_arch35.cpp#L118)
- [FlashAttentionScoreGrad 950 ACLNN 算子知识](../../../operators/aclnn/transformer/attention/flash_attention_score_grad_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TPL_TILING_KEY(...)` 的直接调用（第 237 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attention_score_grad/op_host/flash_attention_score_grad_tiling.cpp#L237)
- [BitwiseOrTensor 950 ACLNN 算子知识](../../../operators/aclnn/math/math/bitwise_or_tensor_950.md)（`related`）：算子声明的固定版本源码包含对 `GET_TPL_TILING_KEY(...)` 的直接调用（第 66 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/bitwise_or/op_host/arch35/bitwise_or_tiling.cpp#L66)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
