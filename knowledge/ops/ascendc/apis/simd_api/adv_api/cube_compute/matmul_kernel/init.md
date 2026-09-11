---
type: API
title: Init
description: 对Matmul对象的Tiling数据进行初始化，根据Tiling参数进行资源划分。Tiling参数可变场景下可多次调用。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.programming_model.execution_unit.cube
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/Init.md
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

# Init

## 功能说明

Init主要用于对Matmul对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分，Tiling参数的具体介绍请参考[Matmul Tiling侧接口](../matmul_tiling/index.md)。

开发者可以先通过[REGIST\_MATMUL\_OBJ](regist_matmul_obj.md)不传入Tiling参数对单个Matmul对象进行初始化，后续通过Init接口单独传入Tiling参数，对Matmul对象中的Tiling数据进行调整。比如，Tiling参数可变的场景下，可以通过多次调用Init来重新设置Tiling参数。

不需要Tiling变更的场景下，推荐使用[REGIST\_MATMUL\_OBJ](regist_matmul_obj.md)传入Tiling参数进行初始化。

## 函数原型

-   Tiling参数传入栈地址

    ```
    __aicore__ inline void Init(const TCubeTiling* __restrict cubeTiling, TPipe* tpipe = nullptr)
    ```

-   Tiling参数传入GM地址

    ```
    __aicore__ inline void Init(const __gm__ TCubeTiling* gmCubeTiling, TPipe* tpipe = nullptr)
    ```

## 参数说明

**表1**  Tiling参数传入栈地址接口参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| cubeTiling | 输入 | Matmul Tiling参数，TCubeTiling结构体定义请参见[表1 TCubeTiling结构说明](../matmul_tiling/t_cube_tiling_struct.md#tcubetiling-struct)。<br><br>Tiling参数可以通过host侧[GetTiling](../matmul_tiling/get_tiling.md)接口获取，并传递到kernel侧使用。在kernel侧调用[GET_TILING_DATA](../../../basic_api/kernel_tiling/get_tiling_data.md)实现将Tiling参数搬运到AI Core内的栈空间中，本接口传入Tiling参数中TCubeTiling结构体的栈地址。 |
| tpipe | 输入 | Tpipe对象。 |

**表2**  Tiling参数传入GM地址接口参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| gmCubeTiling | 输入 | Matmul Tiling参数，该参数指向gm上的一块内存地址，其中的数据类型是TCubeTiling结构体，TCubeTiling结构体定义请参见[表1 TCubeTiling结构说明](../matmul_tiling/t_cube_tiling_struct.md#tcubetiling-struct)。<br><br>Tiling参数可以通过host侧[GetTiling](../matmul_tiling/get_tiling.md)接口获取，并传递到kernel侧使用。在kernel侧调用[GET_TILING_DATA_PTR_WITH_STRUCT](../../../basic_api/kernel_tiling/get_tiling_data_ptr_with_struct.md)获取gm上Tiling参数的指针，本接口传入Tiling参数中TCubeTiling结构体的GM地址。 |
| tpipe | 输入 | Tpipe对象。 |

## 返回值说明

无

## 约束说明

-   Tiling参数传入栈地址的接口：

    无

-   Tiling参数传入GM地址的接口：
    -   仅支持Matmul Tiling参数的[部分常量化](get_matmul_api_tiling.md#功能说明)场景。
    -   不支持CPU域调试。

## 调用示例

-   Tiling参数传入栈地址

    ```
    GET_TILING_DATA(tilingData, tiling);
    // ...
    REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm);
    mm.Init(&(tiling.cubeTilingData));
    ```

-   Tiling参数传入GM地址
    -   纯Cube模式

        ```
        #define ASCENDC_CUBE_ONLY

        GET_TILING_DATA_PTR_WITH_STRUCT(MatmulCustomTilingData, tilingDataPtr, tiling);
        KERNEL_TASK_TYPE_DEFAULT(KERNEL_TYPE_AIC_ONLY);
        // ...
        REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm);
        mm.Init(&(tilingDataPtr->cubeTilingData));
        ```

    -   MIX模式

        ```
        GET_TILING_DATA_PTR_WITH_STRUCT(MatmulCustomTilingData, tilingDataPtr, tiling);
        KERNEL_TASK_TYPE_DEFAULT(KERNEL_TYPE_MIX_AIC_1_2);
        // ...
        // MIX模式下，只调用REGIST_MATMUL_OBJ接口，传入Tiling参数的GM地址，不需调用Init接口
        REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm, &(tilingDataPtr->cubeTilingData));
        ```


<!-- cannbot:related:start -->
## 相关

- [ClearBias](clear_bias.md)（`related`）：Init 页说明“Init主要用于对Matmul对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分”；ClearBias 页明确“如果在调用［Init］(init.md)时配置了TCubeTiling结构中的isBias参数来启用Bias，调用该接口后，会清除Bias标志位，不再启用Bias。”，后者直接修改前者初始化出的 bias 状态。
- [GetMatmulApiTiling](get_matmul_api_tiling.md)（`related`）：Init 的参数合同写明“Tiling参数可以通过host侧GetTiling接口获取，并传递到kernel侧使用。”；GetMatmulApiTiling 页说明“然后调用本接口，得到常量化的Matmul Tiling参数。”，构成 Host/编译期 Tiling 生产到 Kernel Init 消费的直接链。
- [GetTiling](../matmul_tiling/get_tiling.md)（`related`）：“- tiling（输出）：Tiling结构体存储最终的tiling结果。TCubeTiling结构介绍请参考表1。/optiling::TCubeTiling：带有optiling命名空间的TCubeTiling结构体，，该结构体为Host侧定义的Matmul TilingData。”；“- cubeTiling（输入）：Matmul Tiling参数，TCubeTiling结构体定义请参见表1 TCubeTiling结构说明。 Tiling参数可以通过host侧GetTiling接口获取，并传递到kernel侧使用。”。GetTiling 的结果被 Init 直接消费以初始化 Matmul 对象资源。
- [REGIST_MATMUL_OBJ](regist_matmul_obj.md)（`related`）：Init 页说明“开发者可以先通过［REGIST_MATMUL_OBJ］(regist_matmul_obj.md)不传入Tiling参数对单个Matmul对象进行初始化，后续通过Init接口单独传入Tiling参数”；注册页说明“当代码中只有一个Matmul对象时，本接口可以不传入tiling参数，通过Init接口单独传入tiling参数。”，双方明确给出同一注册后再初始化的调用合同。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [FusedLinearCrossEntropyLossGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/fused_linear_cross_entropy_loss_grad.md)（`related`）：算子声明的固定版本源码包含对 `Init(...)` 的直接调用（第 50 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/fused_linear_cross_entropy_loss_grad/op_kernel/fused_linear_cross_entropy_loss_grad_high_perf.h#L50)

### 知识正文中的调用示例

展示 3 / 3 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [Sparse4to2QuantMatmulWeightNz A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/sparse4to2_quant_matmul_weight_nz.md)（`related`）：算子正文包含对 `Init(...)` 的直接调用；本卡提供该接口契约。
- [MhcPreBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mhc/mhc_pre_backward_950.md)（`related`）：算子正文包含对 `Init(...)` 的直接调用；本卡提供该接口契约。
- [TransposeQuantBatchMatMul 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/transpose_quant_batch_mat_mul_950.md)（`related`）：算子正文包含对 `Init(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
