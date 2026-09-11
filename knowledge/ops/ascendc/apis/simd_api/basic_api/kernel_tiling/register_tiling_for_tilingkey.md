---
type: API
title: REGISTER_TILING_FOR_TILINGKEY
description: 用于在kernel侧注册与TilingKey相匹配的TilingData自定义结构体；该接口需提供一个逻辑表达式，逻辑表达式以字符串“TILING_KEY_VAR”代指实际TilingKey，表达TilingKey所满足的范围。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.tiling
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/REGISTER_TILING_FOR_TILINGKEY.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
---

# REGISTER\_TILING\_FOR\_TILINGKEY<a name="ZH-CN_TOPIC_0000002087702626"></a>

## 功能说明<a name="zh-cn_topic_0000001526206862_section212607105720"></a>

用于在kernel侧注册与TilingKey相匹配的TilingData自定义结构体；该接口需提供一个逻辑表达式，逻辑表达式以字符串“TILING\_KEY\_VAR”代指实际TilingKey，表达TilingKey所满足的范围。

## 函数原型<a name="zh-cn_topic_0000001526206862_section1630753514297"></a>

```
REGISTER_TILING_FOR_TILINGKEY(EXPRESSION, TILING_STRUCT)
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
<tbody><tr id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_row152234713443"><td class="cellrowborder" valign="top" width="17.22%" headers="mcps1.1.4.1.1 "><p id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p2340183613156"><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p2340183613156"></a><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p2340183613156"></a>EXPRESSION</p>
</td>
<td class="cellrowborder" valign="top" width="15.340000000000002%" headers="mcps1.1.4.1.2 "><p id="p137163271873"><a name="p137163271873"></a><a name="p137163271873"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="67.44%" headers="mcps1.1.4.1.3 "><p id="p1190216251682"><a name="p1190216251682"></a><a name="p1190216251682"></a>EXPRESSION为逻辑运算，其中用TILING_KEY_VAR指代TilingKey。</p>
</td>
</tr>
<tr id="zh-cn_topic_0000001526206862_row1239183183016"><td class="cellrowborder" valign="top" width="17.22%" headers="mcps1.1.4.1.1 "><p id="p17557191817713"><a name="p17557191817713"></a><a name="p17557191817713"></a>TILING_STRUCT</p>
</td>
<td class="cellrowborder" valign="top" width="15.340000000000002%" headers="mcps1.1.4.1.2 "><p id="zh-cn_topic_0000001526206862_p7239938308"><a name="zh-cn_topic_0000001526206862_p7239938308"></a><a name="zh-cn_topic_0000001526206862_p7239938308"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="67.44%" headers="mcps1.1.4.1.3 "><p id="zh-cn_topic_0000001526206862_p72396320307"><a name="zh-cn_topic_0000001526206862_p72396320307"></a><a name="zh-cn_topic_0000001526206862_p72396320307"></a>用户注册的与TilingKey相匹配的TilingData自定义结构体。</p>
</td>
</tr>
</tbody>
</table>

## 约束说明<a name="zh-cn_topic_0000001526206862_section65498832"></a>

-   使用该接口时，需确保已使用REGISTER\_TILING\_DEFAULT注册默认的用户自定义TilingData结构体，用于告知框架侧用户使用标准C++语法来定义TilingData。
-   EXPRESSION当前支持位运算：&、|、\~、^；移位运算符：<<、\>\>；算术运算：+、-、\*、/、%；条件运算符：==、!=、\>、<、\>=、<=；逻辑与&&、或||以及\(\)。优先级同C++。
-   若TilingData结构体在命名空间内，注册时需要携带对应的命名空间作用域符。
-   不支持同个TilingKey指向不同TilingData结构体，会出现拦截报错。
-   暂不支持kernel直调工程。

## 调用示例<a name="zh-cn_topic_0000001526206862_section97001499599"></a>

```
extern "C" __global__ __aicore__ void add_custom(__gm__ uint8_t *x, __gm__ uint8_t *y, __gm__ uint8_t *z, __gm__ uint8_t *tiling)
{
    REGISTER_TILING_DEFAULT(optiling::TilingData);  // 注册用户默认自定义TilingData结构体
    REGISTER_TILING_FOR_TILINGKEY("TILING_KEY_VAR == 1", optiling::TilingDataA); // 注册TilingKey为1的TilingData结构体
    REGISTER_TILING_FOR_TILINGKEY("(TILING_KEY_VAR >= 10) && (TILING_KEY_VAR <= 15)", optiling::TilingDataB); // 注册TilingKey在[10,15]之间的TilingData结构体
    REGISTER_TILING_FOR_TILINGKEY("TILING_KEY_VAR & 0xFF", optiling::TilingDataC); // 注册TilingKey低8位为1的TilingData结构体
    if (TILING_KEY_IS(1)) {
        GET_TILING_DATA_WITH_STRUCT(optiling::TilingDataA, tilingData, tiling);
        ......
    } else if (TILING_KEY_IS(11)) {
        GET_TILING_DATA_WITH_STRUCT(optiling::TilingDataB, tilingData, tiling);
        ......
    } else if (TILING_KEY_IS(14)) {
        GET_TILING_DATA_WITH_STRUCT(optiling::TilingDataB, tilingData, tiling);
        ......
    } else if (TILING_KEY_IS(255)) {
        GET_TILING_DATA_WITH_STRUCT(optiling::TilingDataC, tilingData, tiling);
        ......
    } else {
        GET_TILING_DATA(tilingData, tiling);
        ......
    }
}
```

使用标准C++语法注册tiling结构体：

```
class TilingDataA{
public:
    ...
};
class TilingDataB{
public:
    ...
};
class TilingDataC{
public:
    ...
};
```

配套的host侧tiling函数示例：

```
ge::graphStatus TilingFunc(gert::TilingContext* context)
{
    // 其他代码逻辑
    ...
    if(condition1){
        context->SetTilingKey(1);
        optiling::TilingDataA *Addtiling = context->GetTilingData<optiling::TilingDataA>();
        ...
    } else if (condition2){
        context->SetTilingKey(11);
        optiling::TilingDataB *Addtiling = context->GetTilingData<optiling::TilingDataB >();
        ...
    } else if (condition3){
        context->SetTilingKey(14);
        optiling::TilingDataB *Addtiling = context->GetTilingData<optiling::TilingDataB >();
        ...
    } else if (condition4){
        context->SetTilingKey(255);
        optiling::TilingDataC *Addtiling = context->GetTilingData<optiling::TilingDataC >();
        ...
    }
    ...
    // 其他代码逻辑
}
```



<!-- cannbot:related:start -->
## 相关

- [REGISTER_TILING_DEFAULT 取小档致 NaN](../../../../runbooks/compilation/register_tiling_default_nan.md)（`exemplifies`）：提供逻辑表达式（以 TILING_KEY_VAR 代指实际 TilingKey）表达 TilingKey 满足的范围；`REGISTER_TILING_FOR_TILINGKEY` 不会把 opParaSize 抬到大档。接口卡说明该宏负责 key 到结构的注册，运行手册补充其不会决定全局 opParaSize 上界，防止把按 key 注册误当成大结构容量修复。
- [REGISTER_TILING_DEFAULT 多 struct 冲突](../../../../runbooks/compilation/register_tiling_default_struct.md)（`exemplifies`）：在 kernel 侧注册与 TilingKey 相匹配的 TilingData 结构体；将 separable 分支的 `REGISTER_TILING_DEFAULT(MaxPool3DGradSeparableTilingData)` 改为 `REGISTER_TILING_FOR_TILINGKEY(<key 字符串>, MaxPool3DGradSeparableTilingData)` 后重新构建，该报错消失、binary 生成恢复。接口卡定义按 TilingKey 注册独立结构，运行手册以多分支 default 槽冲突的真实构建证明该宏是新增结构分支的直接修法。
- [TILING_KEY_IS](tiling_key_is.md)（`same_topic`）：判断本次执行的 tiling_key 是否等于 host 侧设置的某个 key；注册与 TilingKey 相匹配的 TilingData 结构体。REGISTER_TILING_FOR_TILINGKEY 先把 key 条件映射到 TilingData，TILING_KEY_IS 再在 kernel 中选择相同 key 的执行分支；两者共同保证数据结构和代码分支匹配。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 26 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [InplaceIndexFill 950 ACLNN 算子知识](../../../../operators/aclnn/nn/index/inplace_index_fill_950.md)（`related`）：算子声明的固定版本源码包含对 `REGISTER_TILING_FOR_TILINGKEY(...)` 的直接调用（第 71 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/inplace_index_fill/op_kernel/inplace_index_fill_apt.cpp#L71)
- [FlashAttentionScore 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/flash_attention_score_950.md)（`related`）：算子声明的固定版本源码包含对 `REGISTER_TILING_FOR_TILINGKEY(...)` 的直接调用（第 49 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attention_score/op_kernel/flash_attention_score_apt.cpp#L49)
- [QuantMatmul A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/matmul/quant_matmul.md)（`related`）：算子声明的固定版本源码包含对 `REGISTER_TILING_FOR_TILINGKEY(...)` 的直接调用（第 223 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/quant_batch_matmul_v3/op_kernel/quant_batch_matmul_v3.cpp#L223)
- [FlashAttentionScoreGrad A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/flash_attention_score_grad.md)（`related`）：算子声明的固定版本源码包含对 `REGISTER_TILING_FOR_TILINGKEY(...)` 的直接调用（第 509 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attention_score_grad/op_kernel/flash_attention_score_grad.cpp#L509)
- [AdaptiveMaxPool3d A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/pooling/adaptive_max_pool3d.md)（`related`）：算子声明的固定版本源码包含对 `REGISTER_TILING_FOR_TILINGKEY(...)` 的直接调用（第 78 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/pooling/max_pool3d_with_argmax_v2/op_kernel/max_pool3d_with_argmax_v2.cpp#L78)
- [FlashAttentionScoreGrad 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/flash_attention_score_grad_950.md)（`related`）：算子声明的固定版本源码包含对 `REGISTER_TILING_FOR_TILINGKEY(...)` 的直接调用（第 56 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attention_score_grad/op_kernel/flash_attention_score_grad_apt.cpp#L56)
- [MaxPool2dWithIndices A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/pooling/max_pool2d_with_indices.md)（`related`）：算子声明的固定版本源码包含对 `REGISTER_TILING_FOR_TILINGKEY(...)` 的直接调用（第 78 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/pooling/max_pool3d_with_argmax_v2/op_kernel/max_pool3d_with_argmax_v2.cpp#L78)
- [FlashAttentionUnpaddingScoreGrad A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/flash_attention_unpadding_score_grad.md)（`related`）：算子声明的固定版本源码包含对 `REGISTER_TILING_FOR_TILINGKEY(...)` 的直接调用（第 509 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attention_score_grad/op_kernel/flash_attention_score_grad.cpp#L509)
- [MaxPool3dWithArgmax A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/pooling/max_pool3d_with_argmax.md)（`related`）：算子声明的固定版本源码包含对 `REGISTER_TILING_FOR_TILINGKEY(...)` 的直接调用（第 78 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/pooling/max_pool3d_with_argmax_v2/op_kernel/max_pool3d_with_argmax_v2.cpp#L78)
- [FlashAttentionUnpaddingScoreGrad 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/flash_attention_unpadding_score_grad_950.md)（`related`）：算子声明的固定版本源码包含对 `REGISTER_TILING_FOR_TILINGKEY(...)` 的直接调用（第 56 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attention_score_grad/op_kernel/flash_attention_score_grad_apt.cpp#L56)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
