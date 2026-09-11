---
type: API
title: GetSubBlockIdx
description: 在分离模式架构下，获取逻辑AI Core上AIC或AIV的逻辑索引。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetSubBlockIdx_ISASI.md
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

# GetSubBlockIdx(ISASI)

## 功能说明

头文件路径为： `"basic_api/kernel_operator_sys_var_intf.h"`。

在[分离模式架构](../../../../../guides/programming_guide/advanced_programming/hardware_implementation/basic_architecture.md)下，获取逻辑AI Core上Cube Core（AIC）或者Vector Core（AIV）的逻辑索引。

GetSubBlockIdx在使用`__mix__(1, 2)`作为[函数执行空间限定符](../../../../../guides/programming_guide/language_extension/simd_builtin_keywords.md#section1074418132518)的场景下，可以用于区分同一个核上的两个不同Vector Core，取值分别为0和1。

## 函数原型

```cpp
__aicore__ inline int64_t GetSubBlockIdx()
```

## 参数说明

无

## 返回值说明

返回逻辑AI Core上Cube Core（AIC）或者Vector Core（AIV）的逻辑索引。

SubBlockIdx的取值范围为\[0, SubBlockNum\)，SubBlockNum可以通过[GetSubBlockNum](get_sub_block_num_isasi.md)获取。

## 约束说明

无

## 调用示例

```cpp
int64_t subBlockID = AscendC::GetSubBlockIdx();
```


<!-- cannbot:related:start -->
## 相关

- [双AIV CrossCoreFlag 的 subBlock 契约缺陷](../../../../../runbooks/compilation/aiv_crosscoreflag_subblock_507015.md)（`exemplifies`）：焦点卡的修法要求“按 `GetSubBlockIdx() * FLAG_ID_MAX` 偏移区分 V0/V1”，候选卡说明 GetSubBlockIdx 可“区分同一个核上的两个不同Vector Core，取值分别为0和1”；该返回值正是选择两段 flag 池的索引。
- [GetTaskRatio](get_task_ratio.md)（`related`）：GetSubBlockIdx在使用__mix__(1, 2)作为函数执行空间限定符的场景下，可以用于区分同一个核上的两个不同Vector Core，取值分别为0和1。；分离模式下，获取任务启动的Cube Core（AIC）或者Vector Core（AIV）的数量与逻辑AI Core数量的比例。。GetTaskRatio 给出 MIX 分离任务中 AIC/AIV 数量比例，GetSubBlockIdx 再区分同一逻辑核内的两个 Vector Core，联合可解释分核与子核身份。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 25 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [QuantMatmul 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/quant_matmul_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSubBlockIdx(...)` 的直接调用（第 204 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/quant_batch_matmul_v3/op_kernel/arch35/qbmm_mix_online_dynamic.h#L204)
- [BlockSparseAttention A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention.md)（`related`）：算子声明的固定版本源码包含对 `GetSubBlockIdx(...)` 的直接调用（第 927 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention/op_kernel/attn_infra/epilogue/block/bsa_block_epilogue_online_softmax.hpp#L927)
- [QuantMatmulWeightNz 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/quant_matmul_weight_nz_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSubBlockIdx(...)` 的直接调用（第 204 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/quant_batch_matmul_v3/op_kernel/arch35/qbmm_mix_online_dynamic.h#L204)
- [BlockSparseAttention 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSubBlockIdx(...)` 的直接调用（第 96 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention/op_kernel/attn_infra/epilogue/block/block_epilogue_online_softmax_arch35_reg_low_prec.hpp#L96)
- [RotateQuant 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/rotate_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSubBlockIdx(...)` 的直接调用（第 185 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/common/cmct/kernel/kernel_rotate_quant.h#L185)
- [GroupedMatmul 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSubBlockIdx(...)` 的直接调用（第 165 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul/op_kernel/arch35/quant_adaptive_sliding_window_templates/quant_utils.h#L165)
- [TransposeQuantBatchMatMul 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/transpose_quant_batch_mat_mul_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSubBlockIdx(...)` 的直接调用（第 184 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/transpose_quant_batch_mat_mul/op_kernel/arch35/transpose_quant_batch_mat_mul_asw_kernel_advanced.h#L184)
- [GroupedMatmulFinalizeRouting 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul_finalize_routing_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSubBlockIdx(...)` 的直接调用（第 104 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/gmm/common/cgmct/epilogue/block_epilogue_finalize_routing.h#L104)
- [TransposeQuantBatchMatMulWeightNz 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/transpose_quant_batch_mat_mul_weight_nz_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSubBlockIdx(...)` 的直接调用（第 184 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/transpose_quant_batch_mat_mul/op_kernel/arch35/transpose_quant_batch_mat_mul_asw_kernel_advanced.h#L184)
- [grouped_matmul_swiglu_quant 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul_swiglu_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSubBlockIdx(...)` 的直接调用（第 129 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/gmm/common/cgmct/epilogue/block_epilogue_dequant_swiglu.h#L129)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
