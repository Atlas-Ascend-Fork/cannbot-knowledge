---
type: API
title: GetPhyAddr
description: 返回LocalTensor的地址或指定偏移量后的地址。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.development_mode.tensor_programming
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/GetPhyAddr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- '910'
---

# GetPhyAddr<a name="ZH-CN_TOPIC_0000002330927386"></a>

## 功能说明<a name="section618mcpsimp"></a>

返回LocalTensor的地址或指定偏移量后的地址。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
__aicore__ inline uint64_t GetPhyAddr() const
__aicore__ inline uint64_t GetPhyAddr(const uint32_t offset) const
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
<tbody><tr id="row42461942101815"><td class="cellrowborder" valign="top" width="13.94%" headers="mcps1.2.4.1.1 "><p id="p284425844311"><a name="p284425844311"></a><a name="p284425844311"></a>offset</p>
</td>
<td class="cellrowborder" valign="top" width="12.98%" headers="mcps1.2.4.1.2 "><p id="p158449584436"><a name="p158449584436"></a><a name="p158449584436"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="73.08%" headers="mcps1.2.4.1.3 "><p id="p195214291733"><a name="p195214291733"></a><a name="p195214291733"></a>偏移量。</p>
</td>
</tr>
</tbody>
</table>

## 返回值说明<a name="section640mcpsimp"></a>

LocalTensor的地址或指定偏移量后的地址。

## 约束说明<a name="section633mcpsimp"></a>

无

## 调用示例<a name="section17531157161314"></a>

```cpp
// 示例
// 调用GetPhyAddr()返回LocalTensor地址，CPU上返回的是指针类型(T*)，NPU上返回的是物理存储的地址(uint64_t)
#ifdef ASCENDC_CPU_DEBUG
float *inputLocalCpuPtr = inputLocal.GetPhyAddr();
uint64_t realAddr = (uint64_t)inputLocalCpuPtr - (uint64_t)(GetTPipePtr()->GetBaseAddr(static_cast<int8_t>(AscendC::TPosition::VECCALC)));
#else
uint64_t realAddr = inputLocal.GetPhyAddr();
#endif
```


<!-- cannbot:related:start -->
## 相关

- [Gather 双加 LocalTensor 基址导致交错旋转乱码](../../../../../runbooks/precision/localtensor_gather_base_address_not_double_counted.md)（`exemplifies`）：LocalTensor 参数已经确定了源数据的 UB 基址；该重载的有效寻址可按 `src.LocalBase + srcBaseAddr + offsets［i］` 理解。；返回LocalTensor的地址或指定偏移量后的地址。。故障卡的重复基址问题由 GetPhyAddr 返回 LocalTensor 基址的契约直接解释。
- [__aicore__ 禁止 void* 转 __ubuf__ 桥接](../../../../../runbooks/compilation/aicore_void_ubuf.md)（`exemplifies`）：边界与回退：void* 桥接路线 banned，整体回退；改让 wrapper 直接以 `const AscendC::LocalTensor<T>&` 形参接收队列出队的 tensor（dst、x 共用 T；mask 用独立固定类型 `const AscendC::LocalTensor<float>&`），在 wrapper 内部 `GetPhyAddr()` 取 `__ubuf__` 指针——地址空间转换由 LocalTensor 封装负责，不暴露 `void*` 中转。该路线编译推进到下一处错误，证明 void* 根因被消除。；返回LocalTensor的地址或指定偏移量后的地址。。Runbook的修法直接依赖 LocalTensor::GetPhyAddr 保留 UB 地址空间类型，API 卡给出该地址获取合同。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 157 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Resize 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/resize_950.md)（`related`）：算子声明的固定版本源码包含对 `GetPhyAddr(...)` 的直接调用（第 162 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bilinear_v2/op_kernel/arch35/resize_bilinear_v2_broadcast_nchw.h#L162)
- [Cat 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/cat_950.md)（`related`）：算子声明的固定版本源码包含对 `GetPhyAddr(...)` 的直接调用（第 304 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/concat/op_kernel/arch35/one_axis_concat_no_align_diff_shape.h#L304)
- [ClippedSwiglu 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/clipped_swiglu_950.md)（`related`）：算子声明的固定版本源码包含对 `GetPhyAddr(...)` 的直接调用（第 50 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/clipped_swiglu/op_kernel/arch35/clipped_swiglu_kernel.h#L50)
- [BlockSparseAttention 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention_950.md)（`related`）：算子声明的固定版本源码包含对 `GetPhyAddr(...)` 的直接调用（第 188 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention/op_kernel/attn_infra/epilogue/block/block_epilogue_online_softmax_arch35_reg_low_prec.hpp#L188)
- [CircularPad2dBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/circular_pad_2d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `GetPhyAddr(...)` 的直接调用（第 160 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3_grad/op_kernel/arch35/pad_v3_grad_circular_huge_width.h#L160)
- [GeGluBackward A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/ge_glu_backward.md)（`related`）：算子声明的固定版本源码包含对 `GetPhyAddr(...)` 的直接调用（第 474 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/ge_glu_grad_v2/op_kernel/ge_glu_grad_v2_erf_base.h#L474)
- [BlockSparseAttentionGrad 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention_grad_950.md)（`related`）：算子声明的固定版本源码包含对 `GetPhyAddr(...)` 的直接调用（第 293 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention_grad/op_kernel/arc35/vec_op.h#L293)
- [DiagFlat A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/diag_flat.md)（`related`）：算子声明的固定版本源码包含对 `GetPhyAddr(...)` 的直接调用（第 335 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/diag_flat/op_kernel/diag_flat_nd_to_2d.h#L335)
- [GeGluBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/ge_glu_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `GetPhyAddr(...)` 的直接调用（第 474 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/ge_glu_grad_v2/op_kernel/arch35/ge_glu_grad_v2_erf_base.h#L474)
- [FlashAttentionScore 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attention_score_950.md)（`related`）：算子声明的固定版本源码包含对 `GetPhyAddr(...)` 的直接调用（第 112 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/common/op_kernel/arch35/dropmask.h#L112)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
