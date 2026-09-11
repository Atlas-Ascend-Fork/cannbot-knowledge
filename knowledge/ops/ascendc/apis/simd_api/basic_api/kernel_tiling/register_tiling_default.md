---
type: API
title: REGISTER_TILING_DEFAULT
description: 用于在kernel侧注册用户使用标准C++语法自定义的默认TilingData结构体。 注册TilingData结构体用于告知框架侧用户使用标准C++语法来定义TilingData，同时告知框架TilingData结构体类型，用于框架做tiling数据解析。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.tiling
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/REGISTER_TILING_DEFAULT.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
---

# REGISTER\_TILING\_DEFAULT<a name="ZH-CN_TOPIC_0000002123262037"></a>

## 功能说明<a name="zh-cn_topic_0000001526206862_section212607105720"></a>

用于在kernel侧注册用户使用标准C++语法自定义的默认TilingData结构体。

注册TilingData结构体用于告知框架侧用户使用标准C++语法来定义TilingData，同时告知框架TilingData结构体类型，用于框架做tiling数据解析。

## 函数原型<a name="zh-cn_topic_0000001526206862_section1630753514297"></a>

```
REGISTER_TILING_DEFAULT(TILING_STRUCT)
```

## 参数说明<a name="zh-cn_topic_0000001526206862_section129451113125413"></a>

<a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_table111938719446"></a>
<table><thead align="left"><tr id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_row6223476444"><th class="cellrowborder" valign="top" width="17.22%" id="mcps1.1.4.1.1"><p id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p10223674448"><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p10223674448"></a><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p10223674448"></a>参数</p>
</th>
<th class="cellrowborder" valign="top" width="15.32%" id="mcps1.1.4.1.2"><p id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p645511218169"><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p645511218169"></a><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p645511218169"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="67.46%" id="mcps1.1.4.1.3"><p id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p1922337124411"><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p1922337124411"></a><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p1922337124411"></a>说明</p>
</th>
</tr>
</thead>
<tbody><tr id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_row152234713443"><td class="cellrowborder" valign="top" width="17.22%" headers="mcps1.1.4.1.1 "><p id="p18315519741"><a name="p18315519741"></a><a name="p18315519741"></a><span>TILING_STRUCT</span></p>
</td>
<td class="cellrowborder" valign="top" width="15.32%" headers="mcps1.1.4.1.2 "><p id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p320343694214"><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p320343694214"></a><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p320343694214"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="67.46%" headers="mcps1.1.4.1.3 "><p id="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p2684123934216"><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p2684123934216"></a><a name="zh-cn_topic_0000001526206862_zh-cn_topic_0000001389783361_p2684123934216"></a><span>用户注册的默认自定义</span><span>TilingData结构体</span>。</p>
</td>
</tr>
</tbody>
</table>

## 约束说明<a name="zh-cn_topic_0000001526206862_section65498832"></a>

-   若TilingData结构体在命名空间内，注册时需要携带对应的命名空间作用域符。
-   暂不支持核函数（Kernel）直调工程。

## 调用示例<a name="zh-cn_topic_0000001526206862_section97001499599"></a>

```
extern "C" __global__ __aicore__ void add_custom(__gm__ uint8_t *x, __gm__ uint8_t *y, __gm__ uint8_t *z, __gm__ uint8_t *tiling)
{
    REGISTER_TILING_DEFAULT(optiling::TilingData); // 用于在kernel侧注册用户使用标准C++语法自定义的默认TilingData结构体
    GET_TILING_DATA(tilingData, tiling);
    KernelAdd op;
    op.Init(x, y, z, tilingData.blkDim, tilingData.totalSize, tilingData.splitTile);
    op.Process();
}
```



<!-- cannbot:related:start -->
## 相关

- [ACLNN 507035 — stub kernel tiling 数据未初始化](../../../../runbooks/compilation/aclnn_507035_stub_tilingfunc_must_init_tiling_buffer.md)（`exemplifies`）：stub TilingFunc 必须调用 `context->GetTilingData<TilingDataT>()` 取得指针并写入至少一个字段（如 `totalLength`），再 `SetBlockDim`/workspace；kernel 侧保持接口桩不变。修复后 11/11 冒烟通过。；用于在kernel侧注册用户使用标准C++语法自定义的默认TilingData结构体。 注册TilingData结构体用于告知框架侧用户使用标准C++语法来定义TilingData，同时告知框架TilingData结构体类型，用于框架做tiling数据解析。。运行手册的修复要求 Host 初始化与 Kernel 接口桩保持同一 TilingDataT，REGISTER_TILING_DEFAULT 卡说明该注册向框架声明结构体类型供解析，因而支撑 507035 复现与修复中的类型注册步骤。
- [REGISTER_TILING_DEFAULT 取小档致 NaN](../../../../runbooks/compilation/register_tiling_default_nan.md)（`exemplifies`）：用于在kernel侧注册用户使用标准C++语法自定义的默认TilingData结构体；修复前 `opParaSize=132` 对所有 binary 成立。接口卡定义 default TilingData 注册，运行手册展示 default 选成小档后框架推导出的 opParaSize 截断大档结构并造成全 NaN 的实证。
- [REGISTER_TILING_DEFAULT 多 struct 冲突](../../../../runbooks/compilation/register_tiling_default_struct.md)（`exemplifies`）：用于在kernel侧注册用户使用标准C++语法自定义的默认TilingData结构体；若存在 ≥2 个**不同**的 struct 被注册为 default，即为根因。接口卡定义 default 注册槽位，运行手册把同一算子多分支注册不同 struct 的 opbuild 冲突收敛到该槽位唯一性。
- [FastGelu 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/fast_gelu_950.md)（`related`）：“Host 的 `GetTilingData<EleBaseTilingDataV2>` 与 entry 的 `REGISTER_TILING_DEFAULT/GET_TILING_DATA_WITH_STRUCT` 使用同一声明。”说明 FastGelu 注册与读取共享 ABI；“用于在kernel侧注册用户使用标准C++语法自定义的默认TilingData结构体。”给出 REGISTER_TILING_DEFAULT 在该链中的职责。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 161 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Im2colBackward 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/im2col_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `REGISTER_TILING_DEFAULT(...)` 的直接调用（第 32 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/col2im/op_kernel/col2im.cpp#L32)
- [CircularPad2dBackward 950 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/circular_pad_2d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `REGISTER_TILING_DEFAULT(...)` 的直接调用（第 64 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3_grad/op_kernel/pad_v3_grad_apt.cpp#L64)
- [ClippedSwiglu 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/clipped_swiglu_950.md)（`related`）：算子声明的固定版本源码包含对 `REGISTER_TILING_DEFAULT(...)` 的直接调用（第 30 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/clipped_swiglu/op_kernel/clipped_swiglu_apt.cpp#L30)
- [ChunkGatedDeltaRule A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/chunk_gated_delta_rule.md)（`related`）：算子声明的固定版本源码包含对 `REGISTER_TILING_DEFAULT(...)` 的直接调用（第 27 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/chunk_gated_delta_rule/op_kernel/chunk_gated_delta_rule.cpp#L27)
- [UpsampleBicubic2dAA 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/upsample_bicubic_2d_aa_950.md)（`related`）：算子声明的固定版本源码包含对 `REGISTER_TILING_DEFAULT(...)` 的直接调用（第 31 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bicubic2d_aa/op_kernel/upsample_bicubic2d_aa_apt.cpp#L31)
- [ReflectionPad2dBackward 950 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/reflection_pad_2d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `REGISTER_TILING_DEFAULT(...)` 的直接调用（第 64 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3_grad/op_kernel/pad_v3_grad_apt.cpp#L64)
- [HardswishBackward 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/hardswish_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `REGISTER_TILING_DEFAULT(...)` 的直接调用（第 44 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/hard_swish_grad/op_kernel/hard_swish_grad_apt.cpp#L44)
- [FlashAttentionScore 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/flash_attention_score_950.md)（`related`）：算子声明的固定版本源码包含对 `REGISTER_TILING_DEFAULT(...)` 的直接调用（第 46 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attention_score/op_kernel/flash_attention_score_apt.cpp#L46)
- [UpsampleBicubic2dAAGrad 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/upsample_bicubic_2d_aa_grad_950.md)（`related`）：算子声明的固定版本源码包含对 `REGISTER_TILING_DEFAULT(...)` 的直接调用（第 30 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bicubic2d_aa_grad/op_kernel/upsample_bicubic2d_aa_grad_apt.cpp#L30)
- [All 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/all_950.md)（`related`）：算子声明的固定版本源码包含对 `REGISTER_TILING_DEFAULT(...)` 的直接调用（第 27 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/fill/op_kernel/fill_apt.cpp#L27)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
