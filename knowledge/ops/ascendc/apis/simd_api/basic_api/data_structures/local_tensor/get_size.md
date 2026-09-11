---
type: API
title: GetSize
description: 获取当前LocalTensor Size大小。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.development_mode.tensor_programming
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/GetSize.md
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

# GetSize<a name="ZH-CN_TOPIC_0000002330927374"></a>

## 功能说明<a name="section618mcpsimp"></a>

获取当前LocalTensor Size大小。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
__aicore__ inline uint32_t GetSize() const
```

## 参数说明<a name="section622mcpsimp"></a>

无

## 返回值说明<a name="section640mcpsimp"></a>

当前LocalTensor Size大小。单位为元素。

## 约束说明<a name="section633mcpsimp"></a>

无

## 调用示例<a name="section17531157161314"></a>

参考[调用示例](local_tensor_constructor.md#section17531157161314)。

```cpp
// 示例
auto size = inputLocal.GetSize(); // 获取inputLocal的长度，size大小为inputLocal有多少个元素
// 示例5结果如下：
// size大小为srcLen，256。
```



<!-- cannbot:related:start -->
## 相关

- [SetSize](set_size.md)（`related`）：返回值：当前LocalTensor Size大小。单位为元素。；设置当前LocalTensor Size大小。单位为元素。当用户重用local tensor变量且使用长度发生变化的时候，需要使用此接口重新设置Size。。SetSize 在 LocalTensor 重用长度变化时更新元素数，GetSize 读取同一元素单位的当前值，构成 Size 属性的写后读操作。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 16 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [UpsampleBicubic2dAAGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bicubic_2d_aa_grad.md)（`related`）：算子声明的固定版本源码包含对 `GetSize(...)` 的直接调用（第 488 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bicubic2d_aa_grad/op_kernel/upsample_bicubic2d_aa_grad.h#L488)
- [DiagFlat A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/diag_flat.md)（`related`）：算子声明的固定版本源码包含对 `GetSize(...)` 的直接调用（第 323 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/diag_flat/op_kernel/diag_flat_nd_to_2d.h#L323)
- [WeightQuantBatchMatmul A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/weight_quant_batch_matmul.md)（`related`）：算子声明的固定版本源码包含对 `GetSize(...)` 的直接调用（第 740 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/weight_quant_batch_matmul_v2/op_kernel/weight_quant_batch_matmul_v2_common.h#L740)
- [IncreFlashAttention A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/incre_flash_attention.md)（`related`）：算子声明的固定版本源码包含对 `GetSize(...)` 的直接调用（第 1219 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/incre_flash_attention/op_kernel/incre_flash_attention_allvec_new.h#L1219)
- [UpsampleBilinear2dAA A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bilinear_2d_aa.md)（`related`）：算子声明的固定版本源码包含对 `GetSize(...)` 的直接调用（第 404 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bilinear2d_aa/op_kernel/upsample_bilinear2d_aa.h#L404)
- [WeightQuantBatchMatmul 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/weight_quant_batch_matmul_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSize(...)` 的直接调用（第 266 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/weight_quant_batch_matmul_v2/op_kernel/weight_quant_batch_matmul_v2_custom_weight_nz.h#L266)
- [InplaceWeightQuantMatmulAllReduceAddRmsNorm A2 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/inplace_weight_quant_matmul_all_reduce_add_rms_norm.md)（`related`）：算子声明的固定版本源码包含对 `GetSize(...)` 的直接调用（第 740 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/3rd/weight_quant_batch_matmul_v2/op_kernel/weight_quant_batch_matmul_v2_common.h#L740)
- [UpsampleBilinear2dAABackward A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bilinear_2d_aa_backward.md)（`related`）：算子声明的固定版本源码包含对 `GetSize(...)` 的直接调用（第 314 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bilinear2d_aa_backward/op_kernel/upsample_bilinear2d_aa_backward.h#L314)
- [WeightQuantBatchMatmulNz 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/weight_quant_batch_matmul_nz_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSize(...)` 的直接调用（第 740 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/weight_quant_batch_matmul_v2/op_kernel/weight_quant_batch_matmul_v2_common.h#L740)
- [MoeDistributeCombine A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/moe_distribute_combine.md)（`related`）：算子声明的固定版本源码包含对 `GetSize(...)` 的直接调用（第 605 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_combine_v2/op_kernel/moe_distribute_combine_a2_layered.h#L605)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
