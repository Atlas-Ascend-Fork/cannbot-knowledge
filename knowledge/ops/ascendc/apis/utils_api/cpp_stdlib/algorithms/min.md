---
type: API
title: Utils APImin
description: 比较相同数据类型的两个数，返回最小值。
tags:
- task.lookup
- topic.implementation.api_layer.utils_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/algorithms/min.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
---

# min

## 功能说明

比较相同数据类型的两个数，返回最小值。

## 函数原型

```
template <typename T, typename U>
__host__ __aicore__ inline constexpr auto min(const T& src0, const U& src1)
```

## 参数说明

**表1**  模板参数说明

| 参数名 | 含义 |
| --- | --- |
| T | 输入数据src0的数据类型。当前支持的数据类型为<br><br>bool、int8_t、uint8_t、int16_t、uint16_t、int32_t、uint32_t、float、int64_t、uint64_t。 |
| U | 输入数据src1的数据类型。当前支持的数据类型为<br><br>bool、int8_t、uint8_t、int16_t、uint16_t、int32_t、uint32_t、float、int64_t、uint64_t。<br><br>预留类型，当前必须与T保持一致。 |

**表2**  接口参数说明

| 参数名 | 输入/输出 | 含义 |
| --- | --- | --- |
| src0 | 输入 | 源操作数。参与比较的输入。 |
| src1 | 输入 | 源操作数。参与比较的输入。 |

## 约束说明

两个源操作数的数据类型必须相同。

## 返回值说明

两个输入数据中的最小值。

## 调用示例

```
int64_t src0 = 1;
int64_t src1 = 2;

int64_t result = AscendC::Std::min(src0, src1);
// result: 1
```


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 26 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Rasterizer A2/A3 ACLNN 算子知识](../../../../operators/aclnn/cv/image/rasterizer.md)（`related`）：算子声明的固定版本源码包含对 `min(...)` 的直接调用（第 423 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/rasterizer/op_kernel/rasterizer.h#L423)
- [ReflectionPad2dBackward 950 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/reflection_pad_2d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `min(...)` 的直接调用（第 909 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3_grad/op_kernel/arch35/pad_v3_grad_mirror_gather.h#L909)
- [SwigluGroupQuant 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/swiglu_group_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `min(...)` 的直接调用（第 103 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/swiglu_group_quant/op_kernel/arch35/swiglu_dynamic_group_quant_hifp8.h#L103)
- [AttentionUpdate 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/attention_update_950.md)（`related`）：算子声明的固定版本源码包含对 `min(...)` 的直接调用（第 80 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/attention_update/op_kernel/arch35/attention_update_with_lse_regbase.h#L80)
- [ReplicationPad2d 950 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/replication_pad_2d_950.md)（`related`）：算子声明的固定版本源码包含对 `min(...)` 的直接调用（第 62 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3/op_kernel/arch35/pad_edge_gather.h#L62)
- [IndexFill 950 ACLNN 算子知识](../../../../operators/aclnn/nn/index/index_fill_950.md)（`related`）：算子声明的固定版本源码包含对 `min(...)` 的直接调用（第 129 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/index_fill/op_kernel/arch35/index_fill_simt_dense_indices.h#L129)
- [BlockSparseAttention A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/block_sparse_attention.md)（`related`）：算子声明的固定版本源码包含对 `min(...)` 的直接调用（第 939 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention/op_kernel/attn_infra/epilogue/block/bsa_block_epilogue_online_softmax.hpp#L939)
- [ReplicationPad3d 950 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/replication_pad_3d_950.md)（`related`）：算子声明的固定版本源码包含对 `min(...)` 的直接调用（第 62 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3/op_kernel/arch35/pad_edge_gather.h#L62)
- [IndexFillTensor 950 ACLNN 算子知识](../../../../operators/aclnn/nn/index/index_fill_tensor_950.md)（`related`）：算子声明的固定版本源码包含对 `min(...)` 的直接调用（第 129 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/index_fill/op_kernel/arch35/index_fill_simt_dense_indices.h#L129)
- [GroupedMatmul 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/gmm/grouped_matmul_950.md)（`related`）：算子声明的固定版本源码包含对 `min(...)` 的直接调用（第 141 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/gmm/common/cgmct/block/block_scheduler_grouped_matmul_aswt.h#L141)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
