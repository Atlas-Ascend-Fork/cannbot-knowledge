---
type: API
title: FreeTensor
description: 释放TQueBind队列中的指定Tensor。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.memory_management
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQueBind/FreeTensor.md
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
- include/basic_api/kernel_tpipe.h
---

# FreeTensor<a name="ZH-CN_TOPIC_0000001857672837"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_tpipe.h"`。

释放Que中的指定Tensor。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
template <typename T>
__aicore__ inline void FreeTensor(LocalTensor<T>& tensor)
```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  模板参数说明

<a name="table1550165916920"></a>
<table><thead align="left"><tr id="row115015591391"><th class="cellrowborder" valign="top" width="12.139999999999999%" id="mcps1.2.3.1.1"><p id="p12501159099"><a name="p12501159099"></a><a name="p12501159099"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="87.86%" id="mcps1.2.3.1.2"><p id="p85019592918"><a name="p85019592918"></a><a name="p85019592918"></a>说明</p>
</th>
</tr>
</thead>
<tbody><tr id="row1550117591914"><td class="cellrowborder" valign="top" width="12.139999999999999%" headers="mcps1.2.3.1.1 "><p id="p185019592913"><a name="p185019592913"></a><a name="p185019592913"></a>T</p>
</td>
<td class="cellrowborder" valign="top" width="87.86%" headers="mcps1.2.3.1.2 "><p id="p12101541625"><a name="p12101541625"></a><a name="p12101541625"></a><span>Tensor的数据类型，支持的类型请见<a href="../../data_structures/local_tensor/index.md">LocalTensor</a>相关描述。</span></p>
</td>
</tr>
</tbody>
</table>

**表2**  参数说明

<a name="table193329316393"></a>
<table><thead align="left"><tr id="row123331131153919"><th class="cellrowborder" valign="top" width="12.36%" id="mcps1.2.4.1.1"><p id="p8333133153913"><a name="p8333133153913"></a><a name="p8333133153913"></a>参数名称</p>
</th>
<th class="cellrowborder" valign="top" width="12.379999999999999%" id="mcps1.2.4.1.2"><p id="p518118718459"><a name="p518118718459"></a><a name="p518118718459"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="75.26%" id="mcps1.2.4.1.3"><p id="p833353113393"><a name="p833353113393"></a><a name="p833353113393"></a>含义</p>
</th>
</tr>
</thead>
<tbody><tr id="row11660173845017"><td class="cellrowborder" valign="top" width="12.36%" headers="mcps1.2.4.1.1 "><p id="p466053810507"><a name="p466053810507"></a><a name="p466053810507"></a>tensor</p>
</td>
<td class="cellrowborder" valign="top" width="12.379999999999999%" headers="mcps1.2.4.1.2 "><p id="p885774605014"><a name="p885774605014"></a><a name="p885774605014"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="75.26%" headers="mcps1.2.4.1.3 "><p id="p0660153818501"><a name="p0660153818501"></a><a name="p0660153818501"></a>待释放的Tensor。</p>
</td>
</tr>
</tbody>
</table>

## 约束说明<a name="section633mcpsimp"></a>

无

## 返回值说明<a name="section640mcpsimp"></a>

无

## 调用示例<a name="section642mcpsimp"></a>

```cpp
// 使用FreeTensor释放通过AllocTensor分配的Tensor，注意配对使用
AscendC::TPipe pipe;
AscendC::TQueBind<AscendC::TPosition::VECOUT, AscendC::TPosition::GM, 2> que;
int num = 4;
int len = 1024;
pipe.InitBuffer(que, num, len);
AscendC::LocalTensor<half> tensor1 = que.AllocTensor<half>();
que.FreeTensor<half>(tensor1);
```


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 73 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Resize 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/resize_950.md)（`related`）：算子声明的固定版本源码包含对 `FreeTensor(...)` 的直接调用（第 93 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bilinear_v2/op_kernel/arch35/resize_bilinear_v2_all_copy.h#L93)
- [Cat 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/cat_950.md)（`related`）：算子声明的固定版本源码包含对 `FreeTensor(...)` 的直接调用（第 342 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/concat/op_kernel/arch35/one_axis_concat_all_align.h#L342)
- [InplaceSigmoid A2 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/inplace_sigmoid.md)（`related`）：算子声明的固定版本源码包含对 `FreeTensor(...)` 的直接调用（第 93 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/experimental/activation/sigmoid_v2/op_kernel/sigmoid.h#L93)
- [FusedCausalConv1d 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/fused_causal_conv1d_950.md)（`related`）：算子声明的固定版本源码包含对 `FreeTensor(...)` 的直接调用（第 992 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/fused_causal_conv1d/op_kernel/arch35/fused_causal_conv1d_cut_bsh.h#L992)
- [UpsampleBicubic2d 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bicubic_2d_950.md)（`related`）：算子声明的固定版本源码包含对 `FreeTensor(...)` 的直接调用（第 95 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bicubic_v2/op_kernel/arch35/resize_bicubic_v2_all_copy.h#L95)
- [CircularPad2d A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/circular_pad_2d.md)（`related`）：算子声明的固定版本源码包含对 `FreeTensor(...)` 的直接调用（第 68 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/circular_pad/op_kernel/circular_pad.h#L68)
- [Sigmoid A2 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/sigmoid.md)（`related`）：算子声明的固定版本源码包含对 `FreeTensor(...)` 的直接调用（第 93 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/experimental/activation/sigmoid_v2/op_kernel/sigmoid.h#L93)
- [InplaceFusedCausalConv1d 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/inplace_fused_causal_conv1d_950.md)（`related`）：算子声明的固定版本源码包含对 `FreeTensor(...)` 的直接调用（第 992 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/fused_causal_conv1d/op_kernel/arch35/fused_causal_conv1d_cut_bsh.h#L992)
- [UpsampleBicubic2dAA 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bicubic_2d_aa_950.md)（`related`）：算子声明的固定版本源码包含对 `FreeTensor(...)` 的直接调用（第 89 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bicubic2d_aa/op_kernel/arch35/upsample_bicubic2d_aa_data_copy.h#L89)
- [CircularPad2dBackward A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/circular_pad_2d_backward.md)（`related`）：算子声明的固定版本源码包含对 `FreeTensor(...)` 的直接调用（第 175 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/circular_pad_grad/op_kernel/arch32/circular_pad_grad.h#L175)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
