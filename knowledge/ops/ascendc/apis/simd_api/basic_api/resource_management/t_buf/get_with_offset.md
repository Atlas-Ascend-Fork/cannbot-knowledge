---
type: API
title: GetWithOffset
description: 以TBuf为基地址，向后偏移指定长度，将偏移后的地址作为起始地址，提取长度为指定值的Tensor。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.memory_management
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TBuf/GetWithOffset.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- '910'
- kirin_x90
- kirin_9030
source_headers:
- include/basic_api/kernel_tpipe.h
---

# GetWithOffset<a name="ZH-CN_TOPIC_0000001810876828"></a>

## 功能说明<a name="section954881431816"></a>

头文件路径为：`"basic_api/kernel_tpipe.h"`。

以TBuf为基地址，向后偏移指定长度，将偏移后的地址作为起始地址，提取长度为指定值的Tensor。

## 函数原型<a name="section1449617323189"></a>

```cpp
template <typename T>
__aicore__ inline LocalTensor<T> GetWithOffset(uint32_t size, uint32_t bufOffset)
```

## 参数说明<a name="section85121215142514"></a>

**表1**  模板参数说明

<a name="table012895562310"></a>
<table><thead align="left"><tr id="row2128195532318"><th class="cellrowborder" valign="top" width="12.65%" id="mcps1.2.3.1.1"><p id="p1212885512232"><a name="p1212885512232"></a><a name="p1212885512232"></a>参数名称</p>
</th>
<th class="cellrowborder" valign="top" width="87.35000000000001%" id="mcps1.2.3.1.2"><p id="p16129155552315"><a name="p16129155552315"></a><a name="p16129155552315"></a>含义</p>
</th>
</tr>
</thead>
<tbody><tr id="row6129355182310"><td class="cellrowborder" valign="top" width="12.65%" headers="mcps1.2.3.1.1 "><p id="p81291855102318"><a name="p81291855102318"></a><a name="p81291855102318"></a>T</p>
</td>
<td class="cellrowborder" valign="top" width="87.35000000000001%" headers="mcps1.2.3.1.2 "><p id="p14983161812418"><a name="p14983161812418"></a><a name="p14983161812418"></a>待获取Tensor的数据类型，支持的类型请见<a href="../../data_structures/local_tensor/index.md">LocalTensor</a>相关描述。</p>
</td>
</tr>
</tbody>
</table>

**表2**  参数说明

<a name="table1794522316251"></a>
<table><thead align="left"><tr id="row19456238252"><th class="cellrowborder" valign="top" width="12.36%" id="mcps1.2.4.1.1"><p id="p119458239258"><a name="p119458239258"></a><a name="p119458239258"></a>参数名称</p>
</th>
<th class="cellrowborder" valign="top" width="12.379999999999999%" id="mcps1.2.4.1.2"><p id="p9945152332514"><a name="p9945152332514"></a><a name="p9945152332514"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="75.26%" id="mcps1.2.4.1.3"><p id="p1594552312513"><a name="p1594552312513"></a><a name="p1594552312513"></a>含义</p>
</th>
</tr>
</thead>
<tbody><tr id="row1694552372511"><td class="cellrowborder" valign="top" width="12.36%" headers="mcps1.2.4.1.1 "><p id="p1094516239250"><a name="p1094516239250"></a><a name="p1094516239250"></a>size</p>
</td>
<td class="cellrowborder" valign="top" width="12.379999999999999%" headers="mcps1.2.4.1.2 "><p id="p8945112312514"><a name="p8945112312514"></a><a name="p8945112312514"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="75.26%" headers="mcps1.2.4.1.3 "><p id="p169454239253"><a name="p169454239253"></a><a name="p169454239253"></a>需要获取的Tensor元素个数。</p>
</td>
</tr>
<tr id="row165981554174"><td class="cellrowborder" valign="top" width="12.36%" headers="mcps1.2.4.1.1 "><p id="p959810553176"><a name="p959810553176"></a><a name="p959810553176"></a>bufOffset</p>
</td>
<td class="cellrowborder" valign="top" width="12.379999999999999%" headers="mcps1.2.4.1.2 "><p id="p1659820553174"><a name="p1659820553174"></a><a name="p1659820553174"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="75.26%" headers="mcps1.2.4.1.3 "><p id="p125983554175"><a name="p125983554175"></a><a name="p125983554175"></a>从起始位置的偏移长度，单位是字节，且需32字节对齐。</p>
</td>
</tr>
</tbody>
</table>

## 约束说明<a name="section633mcpsimp"></a>

size的数值是Tensor中元素的个数，size\*sizeof\(T\) + bufOffset不能超过TBuf初始化时的长度。

bufOffset需满足32字节对齐的要求。

## 返回值说明<a name="section640mcpsimp"></a>

获取到的[LocalTensor](../../data_structures/local_tensor/index.md)。

## 调用示例<a name="section5725818154718"></a>

```cpp
// 为TBuf初始化分配内存，分配内存长度为1024字节
AscendC::TPipe pipe;
AscendC::TBuf<AscendC::TPosition::VECCALC> calcBuf; // 模板参数为TPosition中的VECCALC类型
uint32_t byteLen = 1024;
pipe.InitBuffer(calcBuf, byteLen);
// 从calcBuf偏移64字节获取Tensor,Tensor为128个int32_t类型元素的内存大小，为512字节
AscendC::LocalTensor<int32_t> tempTensor1 = calcBuf.GetWithOffset<int32_t>(128, 64);
```


<!-- cannbot:related:start -->
## 相关

- [Vector Sub 源 UB 非 32B 对齐触发错误 340](../../../../../runbooks/compilation/vector_sub_ub_32b_340.md)（`exemplifies`）：确认 `TBuf`/`TQue` 的 `InitBuffer` 分配的基址本身 32B 对齐（`Get` / `GetWithOffset(…, 0)` 返回的起始地址对齐），问题只在 `operator［］` 偏移。；bufOffset需满足32字节对齐的要求。。运行手册用 GetWithOffset 的零偏移返回值确认 TBuf 基址对齐，API 卡给出非零 bufOffset 的 32 字节硬约束，从而定位 operator［］ 元素偏移破坏对齐的根因。
- [DequantBias A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/quant/dequant_bias.md)（`related`）：“LocalTensor<WSTYPE> tmpBuf = wsBuf_.GetWithOffset<WSTYPE>(wsTypeNum, wsBufferSize_ / 2);”给出 DequantBias 将 TBuf 一分为二的实际调用；“size*sizeof(T) + bufOffset不能超过TBuf初始化时的长度。”给出该 offset 子视图的越界条件。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 33 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Rasterizer A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/rasterizer.md)（`related`）：算子声明的固定版本源码包含对 `GetWithOffset(...)` 的直接调用（第 236 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/rasterizer/op_kernel/rasterizer.h#L236)
- [ReplicationPad2d 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/replication_pad_2d_950.md)（`related`）：算子声明的固定版本源码包含对 `GetWithOffset(...)` 的直接调用（第 130 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/slice/op_kernel/arch35/slice_move_align_gather.h#L130)
- [InplaceScatterUpdate 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/index/inplace_scatter_update_950.md)（`related`）：算子声明的固定版本源码包含对 `GetWithOffset(...)` 的直接调用（第 409 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/scatter/op_kernel/arch35/scatter.h#L409)
- [BlockSparseAttentionGrad 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention_grad_950.md)（`related`）：算子声明的固定版本源码包含对 `GetWithOffset(...)` 的直接调用（第 87 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention_grad/op_kernel/arc35/block_sparse_attention_grad.h#L87)
- [ReplicationPad3d 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/replication_pad_3d_950.md)（`related`）：算子声明的固定版本源码包含对 `GetWithOffset(...)` 的直接调用（第 130 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/slice/op_kernel/arch35/slice_move_align_gather.h#L130)
- [CrossEntropyLoss A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/loss/cross_entropy_loss.md)（`related`）：算子声明的固定版本源码包含对 `GetWithOffset(...)` 的直接调用（第 129 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/loss/cross_entropy_loss/op_kernel/cross_entropy_loss.h#L129)
- [ChunkGatedDeltaRule A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/chunk_gated_delta_rule.md)（`related`）：算子声明的固定版本源码包含对 `GetWithOffset(...)` 的直接调用（第 118 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/chunk_gated_delta_rule/op_kernel/chunk_gated_delta_rule.h#L118)
- [AddLora A2 ACLNN 算子知识](../../../../../operators/aclnn/math/math/add_lora.md)（`related`）：算子声明的固定版本源码包含对 `GetWithOffset(...)` 的直接调用（第 226 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/add_lora/op_kernel/add_lora_base.h#L226)
- [FusedLinearOnlineMaxSum A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/fused_linear_online_max_sum.md)（`related`）：算子声明的固定版本源码包含对 `GetWithOffset(...)` 的直接调用（第 322 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/fused_linear_online_max_sum/op_kernel/fused_linear_online_max_sum.h#L322)
- [NsaSelectedAttention A2 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/nsa_selected_attention.md)（`related`）：算子声明的固定版本源码包含对 `GetWithOffset(...)` 的直接调用（第 329 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/nsa_selected_attention/op_kernel/nsa_selected_attention.h#L329)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
