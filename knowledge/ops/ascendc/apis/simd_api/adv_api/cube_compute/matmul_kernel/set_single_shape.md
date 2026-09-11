---
type: API
title: SetSingleShape
description: 设置Matmul单核计算的形状singleCoreM、singleCoreN、singleCoreK，单位为元素。用于运行时修改shape，比如复用Matmul对象来处理尾块。与SetTail接口功能一致，建议使用本接口。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.programming_model.execution_unit.cube
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetSingleShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- kirin_x90
---

# SetSingleShape

## 功能说明

设置Matmul单核计算的形状singleCoreM、singleCoreN、singleCoreK，单位为元素。用于运行时修改shape，比如复用Matmul对象来处理尾块。与SetTail接口功能一致，建议使用本接口。

## 函数原型

```
__aicore__ inline void SetSingleShape(int singleM, int singleN, int singleK)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| singleM | 输入 | 设置的singleCoreM大小，单位为元素。 |
| singleN | 输入 | 设置的singleCoreN大小，单位为元素。 |
| singleK | 输入 | 设置的singleCoreK大小，单位为元素。 |

## 返回值说明

无

## 约束说明

无

## 调用示例

```
REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm, &tiling);

// tailM：M方向上剩余元素个数，tailN：N方向上剩余元素个数，tailK：K方向上剩余元素个数
// 如果是尾核，剩余元素可能会少于单核需要计算的元素。此时，需要使用SetSingleShape重新设置本次计算的元素个数
if (tailM < tiling.singleCoreM || tailN < tiling.singleCoreN || tailK < tiling.singleCoreK) {
    matmulObj.SetSingleShape(tailM, tailN, tailK);
}

mm.SetTensorA(gm_a);
mm.SetTensorB(gm_b);
if (tiling.isBias) {
    mm.SetBias(gmBias);
}
mm.IterateAll(gm_c);
mm.End();
```


<!-- cannbot:related:start -->
## 相关

- [SetTail](set_tail.md)（`same_topic`）：设置Matmul单核计算的形状singleCoreM、singleCoreN、singleCoreK，单位为元素。用于运行时修改shape，比如复用Matmul对象来处理尾块。与SetTail接口功能一致，建议使用本接口。；在不改变Tiling的情况下，重新设置本次计算的singleCoreM/singleCoreN/singleCoreK，以元素为单位。；两接口调整同一 Matmul 对象的单核 M/N/K 形状；SetSingleShape 正文明示与 SetTail 功能一致并给出推荐替代。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [FusedLinearCrossEntropyLossGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/fused_linear_cross_entropy_loss_grad.md)（`related`）：算子声明的固定版本源码包含对 `SetSingleShape(...)` 的直接调用（第 264 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/fused_linear_cross_entropy_loss_grad/op_kernel/fused_linear_cross_entropy_loss_grad_high_perf.h#L264)

### 知识正文中的调用示例

展示 5 / 5 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [UpsampleBilinear2dAABackward A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bilinear_2d_aa_backward.md)（`related`）：算子正文包含对 `SetSingleShape(...)` 的直接调用；本卡提供该接口契约。
- [TransposeBatchMatMul A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/transpose_batch_mat_mul.md)（`related`）：算子正文包含对 `SetSingleShape(...)` 的直接调用；本卡提供该接口契约。
- [MhcPostBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mhc/mhc_post_backward_950.md)（`related`）：算子正文包含对 `SetSingleShape(...)` 的直接调用；本卡提供该接口契约。
- [MhcPreSinkhorn A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mhc/mhc_pre_sinkhorn.md)（`related`）：算子正文包含对 `SetSingleShape(...)` 的直接调用；本卡提供该接口契约。
- [RotaryPositionEmbedding A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/posembedding/rotary_position_embedding.md)（`related`）：算子正文包含对 `SetSingleShape(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
