---
type: API
title: SetValue
description: 设置LocalTensor中的某个值。 该接口仅在LocalTensor的TPosition为VECIN/VECCALC/VECOUT时支持。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.development_mode.tensor_programming
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/SetValue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- '910'
source_headers:
- include/basic_api/kernel_tensor.h
---

# SetValue<a name="ZH-CN_TOPIC_0000002364845697"></a>

## 功能说明<a name="section618mcpsimp"></a>

设置LocalTensor中的某个值。

**该接口仅在LocalTensor的TPosition为VECIN/VECCALC/VECOUT时支持。**

## 函数原型<a name="section620mcpsimp"></a>

```cpp
template <typename T1> __aicore__ inline __inout_pipe__(S)
void SetValue(const uint32_t index, const T1 value) const
```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  参数说明

<a name="zh-cn_topic_0235751031_table33761356"></a>
<table><thead align="left"><tr id="zh-cn_topic_0235751031_row27598891"><th class="cellrowborder" valign="top" width="13.94%" id="mcps1.2.4.1.1"><p id="zh-cn_topic_0235751031_p20917673"><a name="zh-cn_topic_0235751031_p20917673"></a><a name="zh-cn_topic_0235751031_p20917673"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="12.98%" id="mcps1.2.4.1.2"><p id="zh-cn_topic_0235751031_p16609919"><a name="zh-cn_topic_0235751031_p16609919"></a><a name="zh-cn_topic_0235751031_p16609919"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="73.08%" id="mcps1.2.4.1.3"><p id="zh-cn_topic_0235751031_p59995477"><a name="zh-cn_topic_0235751031_p59995477"></a><a name="zh-cn_topic_0235751031_p59995477"></a>描述</p>
</th>
</tr>
</thead>
<tbody><tr id="row42461942101815"><td class="cellrowborder" valign="top" width="13.94%" headers="mcps1.2.4.1.1 "><p id="zh-cn_topic_0000001441184464_p5938528141020"><a name="zh-cn_topic_0000001441184464_p5938528141020"></a><a name="zh-cn_topic_0000001441184464_p5938528141020"></a>index</p>
</td>
<td class="cellrowborder" valign="top" width="12.98%" headers="mcps1.2.4.1.2 "><p id="p158449584436"><a name="p158449584436"></a><a name="p158449584436"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="73.08%" headers="mcps1.2.4.1.3 "><p id="p14360822193719"><a name="p14360822193719"></a><a name="p14360822193719"></a>LocalTensor索引，单位为元素。</p>
</td>
</tr>
<tr id="row184841037192110"><td class="cellrowborder" valign="top" width="13.94%" headers="mcps1.2.4.1.1 "><p id="zh-cn_topic_0000001441184464_p188644116443"><a name="zh-cn_topic_0000001441184464_p188644116443"></a><a name="zh-cn_topic_0000001441184464_p188644116443"></a>value</p>
</td>
<td class="cellrowborder" valign="top" width="12.98%" headers="mcps1.2.4.1.2 "><p id="p18484133715217"><a name="p18484133715217"></a><a name="p18484133715217"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="73.08%" headers="mcps1.2.4.1.3 "><p id="p2411756104110"><a name="p2411756104110"></a><a name="p2411756104110"></a>待设置的数值。</p>
</td>
</tr>
</tbody>
</table>

## 返回值说明<a name="section640mcpsimp"></a>

无

## 约束说明<a name="section633mcpsimp"></a>

不要大量使用SetValue对LocalTensor进行赋值，会使性能下降。若需要大批量赋值，请根据实际场景选择[数据填充基础API接口](../../memory_vector_compute/data_padding/index.md)或数据填充高阶API接口（[Pad](../../../adv_api/tensor_transform/pad.md)、[Broadcast](../../../adv_api/tensor_transform/broadcast.md)），以及在需要生成递增数列的场景，选择[Arange](../../../adv_api/index_compute/arange.md)。

## 调用示例<a name="section17531157161314"></a>

```cpp
// srcLen = 256, num = 100, M=50
// 示例1
for (int32_t i = 0; i < srcLen; ++i) {
    inputLocal.SetValue(i, num); // 对inputLocal中第i个位置进行赋值为num
}
// 示例1结果如下：
// 数据(inputLocal): [100 100 100  ... 100]


// srcLen = 256, num = 99, M=50
// 示例2
for (int32_t i = 0; i < srcLen; ++i) {
    inputLocal(i) = num; // 对inputLocal中第i个位置进行赋值为num
}
// 示例2结果如下：
// 数据(inputLocal): [99 99 99  ... 99]
```


<!-- cannbot:related:start -->
## 相关

- [LocalTensor SetValue 参数颠倒导致索引错乱](../../../../../runbooks/precision/localtensor_setvalue_uses_offset_then_value.md)（`exemplifies`）：`LocalTensor::SetValue` 的真实契约是 `SetValue(offset, value)`，而出错代码按 `SetValue(value, offset)` 调用。；设置 LocalTensor 指定索引的元素值。仅在 TPosition 为 VECIN/VECCALC/VECOUT 时支持。参数 offset 为索引偏移，value 为设置的值。支持 950/a2/a3。。故障卡中的参数顺序错误由 SetValue API 的 offset 索引优先、value 值次之合同直接解释。
- [arch35 GetValue/SetValue 标量bypass禁用](../../../../../runbooks/compilation/arch35_getvalue_setvalue_bypass.md)（`exemplifies`）：设置 LocalTensor 指定索引的元素值。仅在 TPosition 为 VECIN/VECCALC/VECOUT 时支持。参数 offset 为索引偏移，value 为设置的值。支持 950/a2/a3。；在 Ascend950PR（arch35 / RegBase、CANN cann-9.0.0-beta.2）上开发 `softplus_v2_grad` 算子。为绕过 `Select(VSEL_CMPMASK_SPR)` 在标量场景（count==1）的 mask 污染问题，尝试对标量输入用 `LocalTensor::GetValue` / `SetValue` 做标量计算 bypass：当 count==1 时用 GetValue 从 LocalTensor 取标量值、用标量数学函数计算、用 SetValue 写回，绕开 Compare+Select 路径。；API 卡给出合法位置和参数，runbook 说明在 arch35 向量流把它当标量 bypass 会让测试失败数暴涨。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 105 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Rasterizer A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/rasterizer.md)（`related`）：算子声明的固定版本源码包含对 `SetValue(...)` 的直接调用（第 173 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/rasterizer/op_kernel/barycentric_from_imgcoord_kernel.h#L173)
- [DiagFlat A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/diag_flat.md)（`related`）：算子声明的固定版本源码包含对 `SetValue(...)` 的直接调用（第 288 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/diag_flat/op_kernel/diag_flat_nd_to_2d.h#L288)
- [Prelu A2 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/prelu.md)（`related`）：算子声明的固定版本源码包含对 `SetValue(...)` 的直接调用（第 172 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/experimental/activation/prelu/op_kernel/prelu.h#L172)
- [ChunkGatedDeltaRule A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/chunk_gated_delta_rule.md)（`related`）：算子声明的固定版本源码包含对 `SetValue(...)` 的直接调用（第 186 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/chunk_gated_delta_rule/op_kernel/chunk_gated_delta_rule_stage1.h#L186)
- [UpsampleBicubic2dAA A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bicubic_2d_aa.md)（`related`）：算子声明的固定版本源码包含对 `SetValue(...)` 的直接调用（第 332 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bicubic2d_aa/op_kernel/upsample_bicubic2d_aa.h#L332)
- [InplaceTril 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/inplace_tril_950.md)（`related`）：算子声明的固定版本源码包含对 `SetValue(...)` 的直接调用（第 107 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/triu/op_kernel/arch35/split_tiny_shape.h#L107)
- [SwigluGroupQuant 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/swiglu_group_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `SetValue(...)` 的直接调用（第 121 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/swiglu_group_quant/op_kernel/arch35/swiglu_dynamic_group_quant_hifp8.h#L121)
- [FlashAttentionScore 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attention_score_950.md)（`related`）：算子声明的固定版本源码包含对 `SetValue(...)` 的直接调用（第 2183 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/common/op_kernel/arch35/flash_attention_noquant_block_vec_base.h#L2183)
- [UpsampleBicubic2dAAGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bicubic_2d_aa_grad.md)（`related`）：算子声明的固定版本源码包含对 `SetValue(...)` 的直接调用（第 500 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bicubic2d_aa_grad/op_kernel/upsample_bicubic2d_aa_grad.h#L500)
- [InplaceTriu 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/inplace_triu_950.md)（`related`）：算子声明的固定版本源码包含对 `SetValue(...)` 的直接调用（第 107 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/triu/op_kernel/arch35/split_tiny_shape.h#L107)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
