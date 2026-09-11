---
type: API
title: GetSubBlockNum
description: 在分离模式架构下，获取一个逻辑AI Core上AIC或AIV的数量。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetSubBlockNum_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- kirin_x90
- kirin_9030
source_headers:
- include/basic_api/kernel_operator_sys_var_intf.h
---

# GetSubBlockNum(ISASI)

## 功能说明

头文件路径为：`"basic_api/kernel_operator_sys_var_intf.h"`。

在[分离模式架构](../../../../../guides/programming_guide/advanced_programming/hardware_implementation/basic_architecture.md)下，获取当前配置中，一个逻辑AI Core上Cube Core（AIC）或者Vector Core（AIV）的数量。

## 函数原型

```cpp
__aicore__ inline int64_t GetSubBlockNum()
```

## 参数说明

无

## 返回值说明

在融合编译场景下，不同[算子类型](../../../../../guides/programming_guide/language_extension/simd_builtin_keywords.md#section1074418132518)在AIC和AIV上调用该接口的返回值如下：

**表1** 融合编译场景返回值列表

| 算子类型 | 限定符 | AIC | AIV |
| --- | --- | --- | --- |
| Vector算子 | \_\_vector\_\_ | - | 1 |
| Cube算子 | \_\_cube\_\_ | 1 | - |
| Mix算子 | \_\_mix\_\_(0, 1) | - | 1 |
| Mix算子 | \_\_mix\_\_(1, 0) | 1 | - |
| Mix算子 | \_\_mix\_\_(1, 1) | 1 | 1 |
| Mix算子 | \_\_mix\_\_(1, 2) | 1 | 2 |

在自定义算子工程和核函数（Kernel）直调工程场景下，不同核函数（Kernel）类型（通过[设置核函数（Kernel）类型](../../kernel_tiling/set_kernel_type.md)设置）在AIC和AIV上调用该接口的返回值如下：

**表2** 自定义算子工程和核函数（Kernel）直调工程场景返回值列表

| 核函数（Kernel）类型 | KERNEL_TYPE_AIV_ONLY | KERNEL_TYPE_AIC_ONLY | KERNEL_TYPE_MIX_AIC_1_2 | KERNEL_TYPE_MIX_AIC_1_1 | KERNEL_TYPE_MIX_AIC_1_0 | KERNEL_TYPE_MIX_AIV_1_0 |
| --- | --- | --- | --- | --- | --- | --- |
| AIV | 1 | - | 2 | 1 | - | 1 |
| AIC | - | 1 | 1 | 1 | 1 | - |

**注意，两种场景中返回值的含义相同，仅设置类型的方式不同，编写算子时推荐使用融合编译。**

## 约束说明

无

## 调用示例

```cpp
int64_t subBlockNum = AscendC::GetSubBlockNum();
```


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 13 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Rasterizer A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/rasterizer.md)（`related`）：算子声明的固定版本源码包含对 `GetSubBlockNum(...)` 的直接调用（第 47 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/rasterizer/op_kernel/barycentric_from_imgcoord_kernel.h#L47)
- [QuantConvolution A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/conv/quant_convolution.md)（`related`）：算子声明的固定版本源码包含对 `GetSubBlockNum(...)` 的直接调用（第 280 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/conv/conv3d_v2/op_kernel/conv3dv2.h#L280)
- [BlockSparseAttention A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention.md)（`related`）：算子声明的固定版本源码包含对 `GetSubBlockNum(...)` 的直接调用（第 928 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention/op_kernel/attn_infra/epilogue/block/bsa_block_epilogue_online_softmax.hpp#L928)
- [WeightQuantBatchMatmul 950 Direct Invoke 算子知识](../../../../../operators/direct/nn/matmul/weight_quant_batch_matmul_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSubBlockNum(...)` 的直接调用（第 60 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/common/cmct/block/block_scheduler_tail_resplit_expanded.h#L60)
- [BlockSparseAttention 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSubBlockNum(...)` 的直接调用（第 122 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention/op_kernel/arch35/block_sparse_attention_kernel_arch35_full_quant.h#L122)
- [FlashAttn 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attn_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSubBlockNum(...)` 的直接调用（第 314 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attn/op_kernel/arch35/flash_attn_kernel_noquant_gqa.h#L314)
- [FusedInferAttentionScore 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/fused_infer_attention_score_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSubBlockNum(...)` 的直接调用（第 203 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/common/op_kernel/arch35/fia_kernel_fullquant_mx.h#L203)
- [NsaCompressAttentionInfer A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/nsa_compress_attention_infer.md)（`related`）：算子声明的固定版本源码包含对 `GetSubBlockNum(...)` 的直接调用（第 875 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/nsa_compress_attention_infer/op_kernel/nsa_compress_attention_infer.h#L875)
- [AlltoAllQuantMatmul A2 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/allto_all_quant_matmul.md)（`related`）：算子声明的固定版本源码包含对 `GetSubBlockNum(...)` 的直接调用（第 197 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/allto_all_matmul/op_kernel/arch22/block_epilogue_dequant.hpp#L197)
- [MatmulReduceScatter A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/matmul_reduce_scatter.md)（`related`）：算子声明的固定版本源码包含对 `GetSubBlockNum(...)` 的直接调用（第 207 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/matmul_reduce_scatter_v2/op_kernel/matmul_reduce_scatter_aiv_mode_block_epilogue_dequant.h#L207)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
