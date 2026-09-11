---
type: API
title: ASCENDC_TPL_SEL_PARAM
description: Tiling模板编程时，开发者通过调用此接口自动生成并配置TilingKey。 使用该接口需要包含定义模板参数和模板参数组合的头文件。详细内容请参考Tiling模板编程。
tags:
- task.lookup
- topic.implementation.api_layer.utils_api
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_template_programming/ASCENDC_TPL_SEL_PARAM.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms: []
source_headers:
- include/utils/tiling/template_argument.h
---

# ASCENDC\_TPL\_SEL\_PARAM<a name="ZH-CN_TOPIC_0000002193954666"></a>

## 功能说明<a name="zh-cn_topic_0000001867289945_zh-cn_topic_0000001389787297_section36583473819"></a>

Tiling模板编程时，开发者通过调用此接口自动生成并配置TilingKey。

使用该接口需要包含定义模板参数和模板参数组合的头文件。详细内容请参考[Tiling模板编程](index.md)。

## 函数原型<a name="zh-cn_topic_0000001867289945_zh-cn_topic_0000001389787297_section13230182415108"></a>

```
#define ASCENDC_TPL_SEL_PARAM(context, ...)           \
do {                                                  \
    uint64_t key = GET_TPL_TILING_KEY(__VA_ARGS__); \
    context->SetTilingKey(key);                       \
} while(0)
// context指代TilingFunc(gert::TilingContext *context)中的context
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
<tbody><tr id="row172853558203"><td class="cellrowborder" valign="top" width="17.22%" headers="mcps1.1.4.1.1 "><p id="p228575592010"><a name="p228575592010"></a><a name="p228575592010"></a>context</p>
</td>
<td class="cellrowborder" valign="top" width="15.340000000000002%" headers="mcps1.1.4.1.2 "><p id="p112851255142017"><a name="p112851255142017"></a><a name="p112851255142017"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="67.44%" headers="mcps1.1.4.1.3 "><p id="p928555522016"><a name="p928555522016"></a><a name="p928555522016"></a>TilingFunc注册上下文。</p>
</td>
</tr>
<tr id="zh-cn_topic_0000001820490272_zh-cn_topic_0000001389787297_row152234713443"><td class="cellrowborder" valign="top" width="17.22%" headers="mcps1.1.4.1.1 "><p id="p1693913355118"><a name="p1693913355118"></a><a name="p1693913355118"></a>...</p>
</td>
<td class="cellrowborder" valign="top" width="15.340000000000002%" headers="mcps1.1.4.1.2 "><p id="zh-cn_topic_0000001820490272_zh-cn_topic_0000001389787297_p15663137127"><a name="zh-cn_topic_0000001820490272_zh-cn_topic_0000001389787297_p15663137127"></a><a name="zh-cn_topic_0000001820490272_zh-cn_topic_0000001389787297_p15663137127"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="67.44%" headers="mcps1.1.4.1.3 "><p id="p010373710272"><a name="p010373710272"></a><a name="p010373710272"></a>可变长参数，模板参数的具体值，传入时需要与定义模板参数和模板参数组合的头文件中的模板参数顺序保持一致。</p>
</td>
</tr>
</tbody>
</table>

## 返回值说明<a name="zh-cn_topic_0000001867289945_zh-cn_topic_0000001389787297_section25791320141317"></a>

无

## 约束说明<a name="zh-cn_topic_0000001867289945_zh-cn_topic_0000001389787297_section19165124931511"></a>

无

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
    ASCENDC_TPL_SEL_PARAM(context, D_T_X, D_T_Y, D_T_Z, TILE_NUM, IS_SPLIT);
    size_t *currentWorkspace = context->GetWorkspaceSizes(1);
    currentWorkspace[0] = 0;
    return ge::GRAPH_SUCCESS;
}
```



<!-- cannbot:related:start -->
## 相关

- [ACLNN 361001 — tilingKey 与 funcEntry 映射失](../../../runbooks/compilation/aclnn_361001_tilingkey_funcentry_sel_position.md)（`exemplifies`）：“宏展开后调用 GET_TPL_TILING_KEY 计算模板参数对应的 key 值，再通过 context->SetTilingKey 设置。”；“运行时**直接令 `funcEntry = tilingKey`** 查找入口。”。运行手册给出焦点宏下发 key 后与 funcEntry 映射失配导致 361001 的诊断链。
- [缺 ASCENDC_TPL_SEL 致运行时分发静默 no-op 跳过](../../../runbooks/compilation/ascendc_tpl_sel_no_op.md)（`exemplifies`）：“典型用法：在 TilingFunc 中根据数据类型、切分策略等条件确定模板参数值，调用 ASCENDC_TPL_SEL_PARAM(context, D_T_X, D_T_Y, D_T_Z, TILE_NUM, IS_SPLIT) 自动设置 TilingKey。”；“规范要求模板化入口 `template <bool templateType, bool isEmptyTensor, bool isTailR> __global__ __aicore__ void euclidean_norm(...)`，由 `ASCENDC_TPL_SEL` 在 `*_struct.h` 内声明 5 个 sub-kernel 实例、host 用 `SetTilingKey(GET_TPL_TILING_KEY(...))` 运行期选择。”。运行手册以失败实例说明焦点宏所在 Host→key→sub-kernel 链缺失会静默 no-op。
- [HardshrinkBackward 950 ACLNN 算子知识](../../../operators/aclnn/nn/activation/hardshrink_backward_950.md)（`related`）：“-> ASCENDC_TPL_SEL_PARAM(dtype, BUFFER_MODE)”展示 HardshrinkBackward Host selector 的实际调用；“宏展开后调用 GET_TPL_TILING_KEY 计算模板参数对应的 key 值，再通过 context->SetTilingKey 设置。”给出该调用如何生成 TilingKey，可直接核对 dtype 与 BUFFER_MODE 到 Device 模板的路由。
- [GET_TPL_TILING_KEY](get_tpl_tiling_key.md)（`same_topic`）：“宏展开后调用 GET_TPL_TILING_KEY 计算模板参数对应的 key 值，再通过 context->SetTilingKey 设置。”；“该接口将传入的模板参数通过定义的位宽，转成二进制，按照顺序组合后转成uint64数值，即TilingKey。”。目标接口定义焦点宏内部生成 key 的编码步骤。
- [模板参数定义](template_params_definition.md)（`same_topic`）：“使用前需包含定义模板参数和模板参数组合的头文件。”；“通过以下函数原型进行模板参数ASCENDC_TPL_ARGS_DECL和模板参数组合ASCENDC_TPL_ARGS_SEL（即可使用的模板）的定义。”。目标接口生产焦点宏运行前必须具备的模板参数声明与组合。

<!-- cannbot:api-operator:start -->
### 知识正文中的调用示例

展示 3 / 3 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [HardswishBackward 950 ACLNN 算子知识](../../../operators/aclnn/nn/activation/hardswish_backward_950.md)（`related`）：算子正文包含对 `ASCENDC_TPL_SEL_PARAM(...)` 的直接调用；本卡提供该接口契约。
- [InplaceSigmoid A2 ACLNN 算子知识](../../../operators/aclnn/nn/activation/inplace_sigmoid.md)（`related`）：算子正文包含对 `ASCENDC_TPL_SEL_PARAM(...)` 的直接调用；本卡提供该接口契约。
- [MishBackward A2/A3 ACLNN 算子知识](../../../operators/aclnn/nn/activation/mish_backward.md)（`related`）：算子正文包含对 `ASCENDC_TPL_SEL_PARAM(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
