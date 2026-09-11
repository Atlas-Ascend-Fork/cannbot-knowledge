---
type: API
title: SetTensorB
description: 设置矩阵乘的右矩阵B。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.programming_model.execution_unit.cube
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetTensorB.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- kirin_x90
- kirin_9030
---

# SetTensorB

## 功能说明

设置矩阵乘的右矩阵B。

## 函数原型

```
__aicore__ inline void SetTensorB(const GlobalTensor<SrcBT>& gm, bool isTransposeB = false)
```

```
__aicore__ inline void SetTensorB(const LocalTensor<SrcBT>& rightMatrix, bool isTransposeB = false)
```

```
__aicore__ inline void SetTensorB(SrcBT bScalar)
```


Atlas 推理系列产品AI Core不支持SetTensorB\(SrcBT bScalar\)接口原型。



Atlas 200I/500 A2 推理产品，不支持SetTensorB\(SrcBT bScalar\)接口原型。


## 参数说明

**表1**  模板参数说明

| 参数名 | 描述 |
| --- | --- |
| SrcBT | 操作数的数据类型。 |

**表2**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| gm | 输入 | B矩阵。类型为[GlobalTensor](../../../basic_api/data_structures/global_tensor/index.md)。SrcBT参数表示B矩阵的数据类型。<br><br>不同型号支持的数据类型请参考[gm和rightMatrix支持的数据类型](#li12616155731720)。 |
| rightMatrix | 输入 | B矩阵。类型为[LocalTensor](../../../basic_api/data_structures/local_tensor/index.md)，支持的TPosition为TSCM/VECOUT。SrcBT参数表示B矩阵的数据类型。<br><br>不同型号支持的数据类型请参考[gm和rightMatrix支持的数据类型](#li12616155731720)。<br><br>若设置TSCM首地址，默认矩阵可全载，已经位于TSCM，Iterate接口无需再进行GM->L1 Buffer（A1/B1）搬运。 |
| bScalar | 输入 | B矩阵中设置的值。支持传入标量数据，标量数据会被扩展为一个形状为[1, K]的tensor参与矩阵乘计算，tensor的数值均为该标量值。例如，开发者可以通过将bScalar设置为1来实现矩阵A在K方向的reduce sum操作。SrcBT参数表示B矩阵的数据类型。<br>不同型号支持的数据类型请参考[bScalar支持的数据类型](#li12616155731723)。 |
| isTransposeB | 输入 | B矩阵是否需要转置。<br><br>注意：<br>若B矩阵MatmulType的ISTRANS参数设置为true，该参数可以为true也可以为false，即运行时可以转置和非转置交替使用；<br>若B矩阵MatmulType的ISTRANS参数设置为false，该参数只能设置为false，若强行设置为true，精度会有异常；<br>对于非half、非bfloat16_t输入类型的场景，为了确保Tiling侧与核函数（Kernel）侧L1 Buffer空间计算大小保持一致及结果精度正确，该参数取值必须与核函数（Kernel）侧定义B矩阵MatmulType的[ISTRANS](matmul_usage.md#p84551411817)参数以及Tiling侧SetBType()接口的[isTrans](../matmul_tiling/set_b_type.md#p47369411111)参数保持一致，即上述三个参数必须同时设置为true或同时设置为false。 |

## 返回值说明

无

## 约束说明

-   传入的TensorB地址空间大小需要保证不小于singleK \* singleN。

-   gm和rightMatrix支持的数据类型<a id="li12616155731720"></a>

    
    Ascend 950PR/Ascend 950DT，支持的数据类型为：half、bfloat16_t、int8_t、float、fp8_e4m3fn_t、fp8_e5m2_t、hifloat8_t。
    

    
    Atlas A3 训练系列产品/Atlas A3 推理系列产品，支持的数据类型为：int4b_t、half、bfloat16_t、int8_t、float。
    

    
    Atlas A2 训练系列产品/Atlas A2 推理系列产品，支持的数据类型为：int4b_t、half、bfloat16_t、int8_t、float。
    

    
    Atlas 推理系列产品AI Core，支持的数据类型为：half、int8_t、float。
    

    
    Atlas 200I/500 A2 推理产品，支持的数据类型为：half、bfloat16_t、int8_t、float。
    

    
    Kirin X90，支持的数据类型为：half、int8_t。
    

    
    Kirin 9030，支持的数据类型为：half。
    

-   bScalar支持的数据类型<a id="li12616155731723"></a>

    
    Ascend 950PR/Ascend 950DT，支持的数据类型为：half、float。
    

    
    Atlas A3 训练系列产品/Atlas A3 推理系列产品，支持的数据类型为：half、float。
    

    
    Atlas A2 训练系列产品/Atlas A2 推理系列产品，支持的数据类型为：half、float。
    

    
    Atlas 推理系列产品AI Core，不支持该参数。
    

    
    Atlas 200I/500 A2 推理产品，不支持该参数。
    

    
    Kirin X90，支持的数据类型为：half。
    

    
    Kirin 9030，支持的数据类型为：half。
    





## 调用示例

```
REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm, &tiling);
mm.SetTensorA(gm_a);
// 示例一：右矩阵在Global Memory
mm.SetTensorB(gm_b, isTransposeB);
if (tiling.isBias) {
    mm.SetBias(gmBias);
}
mm.IterateAll(gm_c);
mm.End();
// 示例二：右矩阵在Local Memory
mm.SetTensorB(local_a, isTransposeB);
// 示例三：设置标量数据
mm.SetTensorB(scalar_a, isTransposeB);
```


<!-- cannbot:related:start -->
## 相关

- [SetBType](../matmul_tiling/set_b_type.md)（`related`）：- isTransposeB（输入）：B矩阵是否需要转置。 注意：若B矩阵MatmulType的ISTRANS参数设置为true，该参数可以为true也可以为false，即运行时可以转置和非转置交替使用； 若B矩阵MatmulType的ISTRANS参数设置为false，该参数只能设置为false，若强行设置为true，精度会有异常；对于非half、非bfloat16_t输入类型的场景，为了确保Tiling侧与Kernel侧L1 Buffer空间计算大小保持一致及结果精度正确，该参数取值必须与Kernel侧定义B矩阵MatmulType的ISTRANS参数以及Tiling侧SetBType()接口的isTrans参数保持一致，即上述三个参数必须同时设置为true或同时设置为false。；设置B矩阵的位置，数据格式，数据类型，是否转置等信息，这些信息需要和kernel侧的设置保持一致。；Kernel 侧 SetTensorB 明确要求转置设置与 Tiling 侧 SetBType 一致，SetBType 正是声明 B 矩阵布局和转置的 Host 侧契约。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [FusedLinearCrossEntropyLossGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/fused_linear_cross_entropy_loss_grad.md)（`related`）：算子声明的固定版本源码包含对 `SetTensorB(...)` 的直接调用（第 263 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/fused_linear_cross_entropy_loss_grad/op_kernel/fused_linear_cross_entropy_loss_grad_high_perf.h#L263)

### 知识正文中的调用示例（部分算子）

展示 9 / 12 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [UpsampleBilinear2dAABackward A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bilinear_2d_aa_backward.md)（`related`）：算子正文包含对 `SetTensorB(...)` 的直接调用；本卡提供该接口契约。
- [LSTM A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/rnn/lstm.md)（`related`）：算子正文包含对 `SetTensorB(...)` 的直接调用；本卡提供该接口契约。
- [NsaSelectedAttention A2 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/nsa_selected_attention.md)（`related`）：算子正文包含对 `SetTensorB(...)` 的直接调用；本卡提供该接口契约。
- [QuantMatmul 950 Direct Invoke 算子知识](../../../../../operators/direct/nn/matmul/quant_matmul_950.md)（`related`）：算子正文包含对 `SetTensorB(...)` 的直接调用；本卡提供该接口契约。
- [grouped_matmul_add A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul_add.md)（`related`）：算子正文包含对 `SetTensorB(...)` 的直接调用；本卡提供该接口契约。
- [LSTM 950 Direct Invoke 算子知识](../../../../../operators/direct/nn/rnn/lstm_950.md)（`related`）：算子正文包含对 `SetTensorB(...)` 的直接调用；本卡提供该接口契约。
- [grouped_matmul_add 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul_add_950.md)（`related`）：算子正文包含对 `SetTensorB(...)` 的直接调用；本卡提供该接口契约。
- [grouped_matmul_finalize_routing A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul_finalize_routing.md)（`related`）：算子正文包含对 `SetTensorB(...)` 的直接调用；本卡提供该接口契约。
- [GroupedMatMulAlltoAllv A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/grouped_mat_mul_allto_allv.md)（`related`）：算子正文包含对 `SetTensorB(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
