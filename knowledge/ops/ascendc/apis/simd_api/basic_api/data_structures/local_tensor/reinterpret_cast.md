---
type: API
title: ReinterpretCast
description: 将当前Tensor重解释为用户指定的新类型，转换后的Tensor与原Tensor地址及内容完全相同，Tensor的大小（字节数）保持不变。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.development_mode.tensor_programming
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/ReinterpretCast.md
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

# ReinterpretCast<a name="ZH-CN_TOPIC_0000002330767554"></a>

## 功能说明<a name="section618mcpsimp"></a>

将当前Tensor重解释为用户指定的新类型，转换后的Tensor与原Tensor地址及内容完全相同，Tensor的大小（字节数）保持不变。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
template <typename CAST_T> 
__aicore__ inline LocalTensor<CAST_T> ReinterpretCast() const
```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  模板参数说明

<a name="table4835205712588"></a>
<table><thead align="left"><tr id="zh-cn_topic_0000001429830437_row118356578583"><th class="cellrowborder" valign="top" width="16.28%" id="mcps1.2.3.1.1"><p id="zh-cn_topic_0000001429830437_p48354572582"><a name="zh-cn_topic_0000001429830437_p48354572582"></a><a name="zh-cn_topic_0000001429830437_p48354572582"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="83.72%" id="mcps1.2.3.1.2"><p id="zh-cn_topic_0000001429830437_p583535795817"><a name="zh-cn_topic_0000001429830437_p583535795817"></a><a name="zh-cn_topic_0000001429830437_p583535795817"></a>描述</p>
</th>
</tr>
</thead>
<tbody><tr id="zh-cn_topic_0000001429830437_row1835857145817"><td class="cellrowborder" valign="top" width="16.28%" headers="mcps1.2.3.1.1 "><p id="p2177206172414"><a name="p2177206172414"></a><a name="p2177206172414"></a>CAST_T</p>
</td>
<td class="cellrowborder" valign="top" width="83.72%" headers="mcps1.2.3.1.2 "><p id="p106801314162417"><a name="p106801314162417"></a><a name="p106801314162417"></a>用户指定的新类型。</p>
</td>
</tr>
</tbody>
</table>

## 返回值说明<a name="section640mcpsimp"></a>

重解释转换后的Tensor。

## 约束说明<a name="section633mcpsimp"></a>

无

## 调用示例<a name="section17531157161314"></a>

```cpp
// 示例
// input_local为int32_t类型，包含16个元素(64字节)
for (int32_t i = 0; i < 16; ++i) {
    inputLocal.SetValue(i, i); // 对inputLocal中第i个位置进行赋值为i
}


// 调用ReinterpretCast将input_local重解释为int16_t类型
AscendC::LocalTensor<int16_t> interpreTensor = inputLocal.ReinterpretCast<int16_t>();
// 示例结果如下，二者数据完全一致，在物理内存上也是同一地址，仅根据不同类型进行了重解释
// inputLocal:0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15
// interpreTensor:0 0 1 0 2 0 3 0 4 0 5 0 6 0 7 0 8 0 9 0 10 0 11 0 12 0 13 0 14 0 15 0
```


<!-- cannbot:related:start -->
## 相关

- [FreeTensor早释使队列别名被下一轮DMA覆盖](../../../../../runbooks/precision/reinterpret_tensor_alias_must_outlive_queue_release.md)（`exemplifies`）：焦点 API 的核心合同是“转换后的Tensor与原Tensor地址及内容完全相同”，候选故障卡中的“`xT = xIO.ReinterpretCast<CT>()`，这里 `T` 与 `CT` 都是 fp32，`xT` 仍指向 `xIO` 的 UB”正是该别名合同导致 FreeTensor 后仍访问同一 UB 的具体失效实例。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 61 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Rasterizer A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/rasterizer.md)（`related`）：算子声明的固定版本源码包含对 `ReinterpretCast(...)` 的直接调用（第 244 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/rasterizer/op_kernel/rasterizer.h#L244)
- [MaskedSelect A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/masked_select.md)（`related`）：算子声明的固定版本源码包含对 `ReinterpretCast(...)` 的直接调用（第 245 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/masked_select_v3/op_kernel/masked_select_v3.h#L245)
- [DeformableConv2d A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/conv/deformable_conv2d.md)（`related`）：算子声明的固定版本源码包含对 `ReinterpretCast(...)` 的直接调用（第 403 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/conv/deformable_conv2d/op_kernel/deformable_conv2d_base.h#L403)
- [BlockSparseAttention A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention.md)（`related`）：算子声明的固定版本源码包含对 `ReinterpretCast(...)` 的直接调用（第 185 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention/op_kernel/attn_infra/epilogue/block/bsa_block_epilogue_rescale_o.hpp#L185)
- [UpsampleBicubic2dAA A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bicubic_2d_aa.md)（`related`）：算子声明的固定版本源码包含对 `ReinterpretCast(...)` 的直接调用（第 349 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bicubic2d_aa/op_kernel/upsample_bicubic2d_aa.h#L349)
- [GroupedBiasAddGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/math/grouped_bias_add_grad.md)（`related`）：算子声明的固定版本源码包含对 `ReinterpretCast(...)` 的直接调用（第 129 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/grouped_bias_add_grad/op_kernel/arch32/grouped_bias_add_grad_unequal_c_perf.h#L129)
- [EmbeddingBag 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/index/embedding_bag_950.md)（`related`）：算子声明的固定版本源码包含对 `ReinterpretCast(...)` 的直接调用（第 145 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/embedding_bag/op_kernel/arch35/embedding_bag_regbase_1d_mean.h#L145)
- [GroupedMatmul A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul.md)（`related`）：算子声明的固定版本源码包含对 `ReinterpretCast(...)` 的直接调用（第 435 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul/op_kernel/grouped_matmul_antiquant_a8w4_msd_new.h#L435)
- [UpsampleBilinear2dAA A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bilinear_2d_aa.md)（`related`）：算子声明的固定版本源码包含对 `ReinterpretCast(...)` 的直接调用（第 434 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bilinear2d_aa/op_kernel/upsample_bilinear2d_aa.h#L434)
- [Sort 950 ACLNN 算子知识](../../../../../operators/aclnn/math/math/sort_950.md)（`related`）：算子声明的固定版本源码包含对 `ReinterpretCast(...)` 的直接调用（第 261 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/sort/op_kernel/arch35/merge_sort_big_size.h#L261)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
