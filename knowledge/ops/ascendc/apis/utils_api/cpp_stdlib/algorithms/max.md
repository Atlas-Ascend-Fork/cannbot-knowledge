---
type: API
title: Utils APImax
description: 比较相同数据类型的两个数，返回最大值。
tags:
- task.lookup
- topic.implementation.api_layer.utils_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/algorithms/max.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
---

# max

## 功能说明

比较相同数据类型的两个数，返回最大值。

## 函数原型

```
template <typename T, typename U>
__host__ __aicore__ inline constexpr auto max(const T& src0, const U& src1)
```

## 参数说明

**表1**  模板参数说明

| 参数名 | 含义 |
| --- | --- |
| T | 输入数据src0的数据类型。当前支持的数据类型为bool、int8_t、uint8_t、int16_t、uint16_t、int32_t、uint32_t、float、int64_t、uint64_t。 |
| U | 输入数据src1的数据类型。当前支持的数据类型为bool、int8_t、uint8_t、int16_t、uint16_t、int32_t、uint32_t、float、int64_t、uint64_t。<br><br>预留类型，当前必须与T保持一致。 |

**表2**  接口参数说明

| 参数名 | 输入/输出 | 含义 |
| --- | --- | --- |
| src0 | 输入 | 源操作数。参与比较的输入。 |
| src1 | 输入 | 源操作数。参与比较的输入。 |

## 约束说明

两个源操作数的数据类型必须相同。

## 返回值说明

两个输入数据中的最大值。

## 调用示例

```
int64_t src0 = 1;
int64_t src1 = 2;

int64_t result = AscendC::Std::max(src0, src1);
// result: 2
```


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 10 / 10 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Rasterizer A2/A3 ACLNN 算子知识](../../../../operators/aclnn/cv/image/rasterizer.md)（`related`）：算子声明的固定版本源码包含对 `max(...)` 的直接调用（第 423 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/rasterizer/op_kernel/rasterizer.h#L423)
- [ReflectionPad2dBackward 950 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/reflection_pad_2d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `max(...)` 的直接调用（第 984 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3_grad/op_kernel/arch35/pad_v3_grad_mirror_gather.h#L984)
- [SwigluGroupQuant 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/swiglu_group_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `max(...)` 的直接调用（第 120 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/swiglu_group_quant/op_kernel/arch35/swiglu_dynamic_group_quant_hifp8.h#L120)
- [ChunkGatedDeltaRule A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/chunk_gated_delta_rule.md)（`related`）：算子声明的固定版本源码包含对 `max(...)` 的直接调用（第 117 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/chunk_gated_delta_rule/op_kernel/chunk_gated_delta_rule_stage1.h#L117)
- [FusedLinearCrossEntropyLossGrad A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/matmul/fused_linear_cross_entropy_loss_grad.md)（`related`）：算子声明的固定版本源码包含对 `max(...)` 的直接调用（第 65 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/fused_linear_cross_entropy_loss_grad/op_kernel/fused_linear_cross_entropy_loss_grad_mem_friendly.h#L65)
- [MoeDistributeCombine A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/mc2/moe_distribute_combine.md)（`related`）：算子声明的固定版本源码包含对 `max(...)` 的直接调用（第 284 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_combine_v2/op_kernel/moe_distribute_combine_a2.h#L284)
- [AdaLayerNorm A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/norm/ada_layer_norm.md)（`related`）：算子声明的固定版本源码包含对 `max(...)` 的直接调用（第 99 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/norm/ada_layer_norm/op_kernel/ada_layer_norm_base_v1.h#L99)
- [MoeDistributeDispatch A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/mc2/moe_distribute_dispatch.md)（`related`）：算子声明的固定版本源码包含对 `max(...)` 的直接调用（第 275 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_dispatch_v2/op_kernel/moe_distribute_dispatch_a2.h#L275)
- [AdaLayerNormQuant A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/norm/ada_layer_norm_quant.md)（`related`）：算子声明的固定版本源码包含对 `max(...)` 的直接调用（第 99 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/norm/ada_layer_norm/op_kernel/ada_layer_norm_base_v1.h#L99)
- [BatchNorm 950 ACLNN 算子知识](../../../../operators/aclnn/nn/norm/batch_norm_950.md)（`related`）：算子声明的固定版本源码包含对 `max(...)` 的直接调用（第 170 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/norm/batch_norm_v3/op_kernel/arch35/batch_norm_v3_rar_block_split_r.h#L170)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
