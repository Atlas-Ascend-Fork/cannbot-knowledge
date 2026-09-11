---
type: API
title: GetValue
description: 获取GlobalTensor的相应偏移位置的值。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.development_mode.tensor_programming
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/GetValue.md
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

# GetValue<a name="ZH-CN_TOPIC_0000002132084956"></a>

## 功能说明<a name="section618mcpsimp"></a>

获取GlobalTensor的相应偏移位置的值。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
__aicore__ inline __inout_pipe__(S) PrimType GetValue(const uint64_t offset) const
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
<td class="cellrowborder" valign="top" width="73.08%" headers="mcps1.2.4.1.3 "><p id="p126017529210"><a name="p126017529210"></a><a name="p126017529210"></a>偏移offset个元素。</p>
</td>
</tr>
</tbody>
</table>

## 返回值说明<a name="section640mcpsimp"></a>

返回PrimType类型的立即数。

## 约束说明<a name="section633mcpsimp"></a>

如果GetValue的Global Memory地址内容存在被外部改写的可能，需要先调用[DataCacheCleanAndInvalid](../../cache_control/data_cache_clean_and_invalid.md)，确保Data Cache与Global Memory的Cache一致性，之后再调用此接口。

## 调用示例<a name="section1956710347119"></a>

```cpp
// 数据(GlobalTensor): [0 100 200  ... ]

AscendC::GlobalTensor<uint32_t> tiling_global;
tiling_global.SetGlobalBuffer(reinterpret_cast<__gm__ uint32_t *>(tiling), 16);
const uint16_t C1 = (uint16_t)tiling_global.GetValue(0);
const uint16_t H = (uint16_t)tiling_global(1);  
// 示例结果如下：
// C1 = 0，H = 100
```


<!-- cannbot:related:start -->
## 相关

- [DataCacheCleanAndInvalid](../../cache_control/data_cache_clean_and_invalid.md)（`related`）：Scalar单元访问GM，首先会访问每个核内的Data Cache，因此存在Data Cache与GM的Cache一致性问题。；清除并失效Data Cache，确保Scalar单元通过Data Cache读取的GM数据与DMA单元直接写入GM的数据保持一致。当DMA向GM写入数据后，若Scalar需要读取该数据，需先调用本接口清除Data Cache中的旧缓存，否则可能读到过期数据。。GetValue 卡指出 Scalar 读 GM 会经过核内 Data Cache 并产生一致性风险，DataCacheCleanAndInvalid 卡给出 DMA 写后、Scalar 读前清除旧缓存的具体操作，构成读值前的缓存一致性处理链。
- [operator](operator_call.md)（`related`）：返回值为指定索引位置的 PrimType 类型引用，用于左值相当于 SetValue，用于右值相当于 GetValue。；获取GlobalTensor的相应偏移位置的值。。GlobalTensor operator() 卡明确右值语境等价于 GetValue，GetValue 卡给出按偏移读取的语义，二者连接运算符重载与显式读取接口。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 136 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Rasterizer A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/rasterizer.md)（`related`）：算子声明的固定版本源码包含对 `GetValue(...)` 的直接调用（第 483 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/rasterizer/op_kernel/rasterizer.h#L483)
- [MaskedSelect A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/masked_select.md)（`related`）：算子声明的固定版本源码包含对 `GetValue(...)` 的直接调用（第 143 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/masked_select_v3/op_kernel/masked_select_v3.h#L143)
- [FatreluMul A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/fatrelu_mul.md)（`related`）：算子声明的固定版本源码包含对 `GetValue(...)` 的直接调用（第 94 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/fatrelu_mul/op_kernel/fatrelu_mul.h#L94)
- [BlockSparseAttention A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention.md)（`related`）：算子声明的固定版本源码包含对 `GetValue(...)` 的直接调用（第 152 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention/op_kernel/attn_infra/gemm/block/bsa_block_mmad_pv.hpp#L152)
- [AddLora A2 ACLNN 算子知识](../../../../../operators/aclnn/math/math/add_lora.md)（`related`）：算子声明的固定版本源码包含对 `GetValue(...)` 的直接调用（第 573 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/add_lora/op_kernel/add_lora_base.h#L573)
- [GeluQuant 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/gelu_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `GetValue(...)` 的直接调用（第 250 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/gelu_quant/op_kernel/arch35/gelu_quant_base_regbase.h#L250)
- [BlockSparseAttention 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention_950.md)（`related`）：算子声明的固定版本源码包含对 `GetValue(...)` 的直接调用（第 184 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention/op_kernel/arch35/block_sparse_attention_kernel_arch35_full_quant.h#L184)
- [OneHot 950 ACLNN 算子知识](../../../../../operators/aclnn/math/math/one_hot_950.md)（`related`）：算子声明的固定版本源码包含对 `GetValue(...)` 的直接调用（第 90 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/one_hot/op_kernel/arch35/one_hot.h#L90)
- [Heaviside A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/heaviside.md)（`related`）：算子声明的固定版本源码包含对 `GetValue(...)` 的直接调用（第 166 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/heaviside/op_kernel/heaviside.h#L166)
- [BlockSparseAttentionGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention_grad.md)（`related`）：算子声明的固定版本源码包含对 `GetValue(...)` 的直接调用（第 231 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention_grad/op_kernel/arc22/block_sparse_attention_grad_kernel.h#L231)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
