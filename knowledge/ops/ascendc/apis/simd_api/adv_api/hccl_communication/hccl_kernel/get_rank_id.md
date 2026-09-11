---
type: API
title: GetRankId
description: 获取本卡RankId。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/GetRankId.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
source_headers:
- include/adv_api/hccl/hccl.h
---

# GetRankId

## 功能说明

获取本卡RankId。该接口默认在所有核上工作，用户也可以在调用前通过[GetBlockIdx](../../../basic_api/tool_interface/system_resources_and_variables/get_block_idx.md)指定其在某一个核上运行。

## 函数原型

```
__aicore__ inline uint32_t GetRankId()
```

## 参数说明

无

## 返回值说明

返回本卡RankId。

## 约束说明

无

## 调用示例

请参见[GetWindowsInAddr](get_windows_in_addr.md)的调用示例。



<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 9 / 9 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [AlltoAllAllGatherBatchMatMul A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/allto_all_all_gather_batch_mat_mul.md)（`related`）：算子声明的固定版本源码包含对 `GetRankId(...)` 的直接调用（第 213 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/allto_all_all_gather_batch_mat_mul/op_kernel/allto_all_all_gather_batch_mat_mul.h#L213)
- [BatchMatMulReduceScatterAlltoAll A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/batch_mat_mul_reduce_scatter_allto_all.md)（`related`）：算子声明的固定版本源码包含对 `GetRankId(...)` 的直接调用（第 275 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/batch_mat_mul_reduce_scatter_allto_all/op_kernel/batch_mat_mul_reduce_scatter_allto_all.h#L275)
- [InplaceMatmulAllReduceAddRmsNorm A2 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/inplace_matmul_all_reduce_add_rms_norm.md)（`related`）：算子声明的固定版本源码包含对 `GetRankId(...)` 的直接调用（第 57 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/matmul_all_reduce/op_kernel/arch22/matmul_all_reduce_base.h#L57)
- [InplaceQuantMatmulAllReduceAddRmsNorm A2 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/inplace_quant_matmul_all_reduce_add_rms_norm.md)（`related`）：算子声明的固定版本源码包含对 `GetRankId(...)` 的直接调用（第 57 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/matmul_all_reduce/op_kernel/arch22/matmul_all_reduce_base.h#L57)
- [InplaceWeightQuantMatmulAllReduceAddRmsNorm A2 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/inplace_weight_quant_matmul_all_reduce_add_rms_norm.md)（`related`）：算子声明的固定版本源码包含对 `GetRankId(...)` 的直接调用（第 57 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/matmul_all_reduce/op_kernel/arch22/matmul_all_reduce_base.h#L57)
- [MatmulAllReduceAddRmsNorm A2 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/matmul_all_reduce_add_rms_norm.md)（`related`）：算子声明的固定版本源码包含对 `GetRankId(...)` 的直接调用（第 57 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/matmul_all_reduce/op_kernel/arch22/matmul_all_reduce_base.h#L57)
- [QuantMatmulAllReduce A2 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/quant_matmul_all_reduce.md)（`related`）：算子声明的固定版本源码包含对 `GetRankId(...)` 的直接调用（第 57 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/matmul_all_reduce/op_kernel/arch22/matmul_all_reduce_base.h#L57)
- [QuantMatmulAllReduceAddRmsNorm A2 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/quant_matmul_all_reduce_add_rms_norm.md)（`related`）：算子声明的固定版本源码包含对 `GetRankId(...)` 的直接调用（第 57 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/matmul_all_reduce/op_kernel/arch22/matmul_all_reduce_base.h#L57)
- [WeightQuantMatmulAllReduceAddRmsNorm A2 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/weight_quant_matmul_all_reduce_add_rms_norm.md)（`related`）：算子声明的固定版本源码包含对 `GetRankId(...)` 的直接调用（第 57 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/matmul_all_reduce/op_kernel/arch22/matmul_all_reduce_base.h#L57)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
