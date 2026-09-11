---
type: API
title: GetPhyAddr
description: GlobalTensor::GetPhyAddr 接口，用于获取全局数据的物理地址，支持全平台。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.development_mode.tensor_programming
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/GetPhyAddr.md
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

# GetPhyAddr<a name="ZH-CN_TOPIC_0000002167524401"></a>

## 功能说明<a name="section618mcpsimp"></a>

获取全局数据的地址。

## 函数原型<a name="section620mcpsimp"></a>

-   获取全局数据的地址

    ```cpp
    __aicore__ inline const __gm__ PrimType* GetPhyAddr() const
    ```

-   获取全局数据（指定偏移offset个元素）的地址

    ```cpp
    __aicore__ inline __gm__ PrimType* GetPhyAddr(const uint64_t offset) const
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
<tbody><tr id="row42461942101815"><td class="cellrowborder" valign="top" width="13.94%" headers="mcps1.2.4.1.1 "><p id="p151479166327"><a name="p151479166327"></a><a name="p151479166327"></a>offset</p>
</td>
<td class="cellrowborder" valign="top" width="12.98%" headers="mcps1.2.4.1.2 "><p id="p158449584436"><a name="p158449584436"></a><a name="p158449584436"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="73.08%" headers="mcps1.2.4.1.3 "><p id="p126017529210"><a name="p126017529210"></a><a name="p126017529210"></a><span>偏移的元素个数，用于指定数据的位置。</span></p>
</td>
</tr>
</tbody>
</table>

## 返回值说明<a name="section640mcpsimp"></a>

全局数据的地址。

## 约束说明<a name="section633mcpsimp"></a>

无。

## 调用示例<a name="section17531157161314"></a>

```cpp
template <typename T>
__aicore__ inline void CopyIn(const AscendC::GlobalTensor<T>& input)
{
    AscendC::GlobalTensor<T> output;
    output.SetGlobalBuffer(input.GetPhyAddr(0), input.GetSize());
    // ...
}
```


<!-- cannbot:related:start -->
## 相关

- [GetPhyAddr const __gm__ 返回不可去 const](../../../../../runbooks/compilation/getphyaddr_const_gm_const.md)（`exemplifies`）：`AscendC::GlobalTensor<T>::GetPhyAddr()` 的返回类型是 `const __gm__ PrimType*`。C++ 规则下 `reinterpret_cast` 不能 casts away qualifiers（去 const），bisheng 编译器据此拒绝把 `const __gm__ int *` 转成 `__gm__ uint8_t *`。；GlobalTensor::GetPhyAddr 接口，用于获取全局数据的物理地址，支持全平台。；Runbook 用真实编译错误复现 GetPhyAddr 返回地址的 const 限定，并给出从 GM_ADDR 捕获可写裸指针的修复，直接示范该 API 合同的排障。
- [aicore 禁止 const char* cast 到 __gm__ T*](../../../../../runbooks/compilation/aicore_const_char_cast_gm_t.md)（`exemplifies`）：在 aicore kernel 中访问 GM 时，始终从 `__gm__` 限定的来源（`GM_ADDR` 入参、`GlobalTensor<T>::GetPhyAddr()`）派生指针，不要用 `reinterpret_cast` 把非 `__gm__` 指针升级为 `__gm__ T*`。；GlobalTensor::GetPhyAddr 接口，用于获取全局数据的物理地址，支持全平台。。Runbook要求从 `GlobalTensor<T>::GetPhyAddr()` 派生合法 GM 指针，API 卡定义获取该全局数据物理地址的接口。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 83 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Im2colBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/im2col_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `GetPhyAddr(...)` 的直接调用（第 129 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/col2im/op_kernel/arch35/col2im_simt.h#L129)
- [CircularPad2dBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/circular_pad_2d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `GetPhyAddr(...)` 的直接调用（第 426 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3_grad/op_kernel/arch35/pad_v3_grad_circular_simt.h#L426)
- [DeformableConv2d 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/conv/deformable_conv2d_950.md)（`related`）：算子声明的固定版本源码包含对 `GetPhyAddr(...)` 的直接调用（第 190 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/conv/deformable_offsets/op_kernel/arch35/deformable_offsets.h#L190)
- [FlashAttentionScore 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attention_score_950.md)（`related`）：算子声明的固定版本源码包含对 `GetPhyAddr(...)` 的直接调用（第 886 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/common/op_kernel/arch35/flash_attention_noquant_block_cube.h#L886)
- [Resize 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/resize_950.md)（`related`）：算子声明的固定版本源码包含对 `GetPhyAddr(...)` 的直接调用（第 156 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bilinear_v2/op_kernel/arch35/resize_bilinear_v2_simt_hw.h#L156)
- [ConfusionTranspose 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/confusion_transpose_950.md)（`related`）：算子声明的固定版本源码包含对 `GetPhyAddr(...)` 的直接调用（第 269 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/transpose/op_kernel/arch35/transpose_small_shape.h#L269)
- [QuantConvolution 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/conv/quant_convolution_950.md)（`related`）：算子声明的固定版本源码包含对 `GetPhyAddr(...)` 的直接调用（第 240 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/conv/conv3d_v2/op_kernel/arch35/conv3d_v2_instr_dequant_impl.h#L240)
- [FlashAttentionVarLenScore 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attention_var_len_score_950.md)（`related`）：算子声明的固定版本源码包含对 `GetPhyAddr(...)` 的直接调用（第 866 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/common/op_kernel/arch35/flash_attention_score_block_cube.h#L866)
- [UpsampleBicubic2d 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bicubic_2d_950.md)（`related`）：算子声明的固定版本源码包含对 `GetPhyAddr(...)` 的直接调用（第 159 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bicubic_v2/op_kernel/arch35/resize_bicubic_v2_simt_nchw.h#L159)
- [DiagFlat A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/diag_flat.md)（`related`）：算子声明的固定版本源码包含对 `GetPhyAddr(...)` 的直接调用（第 335 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/diag_flat/op_kernel/diag_flat_nd_to_2d.h#L335)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
