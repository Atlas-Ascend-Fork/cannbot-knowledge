---
type: API
title: Iterate
description: 每调用一次计算一块baseM*baseN的C矩阵，内部维护迭代进度并偏移A、B矩阵首地址。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.programming_model.execution_unit.cube
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/Iterate.md
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

# Iterate

## 功能说明

每调用一次Iterate，会计算出一块baseM \* baseN的C矩阵。接口内部会维护迭代进度，调用一次后会对A、B矩阵首地址进行偏移。默认以先M轴再N轴的迭代顺序，也可以通过调整tiling参数iterateOrder，转换为先N轴再M轴的迭代顺序。当传入数据未对齐，存在尾块时，会在最后一次迭代输出尾块的计算结果。

一次Iterate矩阵乘的结果C矩阵存放在L0C Buffer（CO1）中，对于L0C Buffer（CO1）中计算结果的获取，当前支持如下两种方式：

-   用户无需自行管理存放矩阵乘结果的L0C Buffer（CO1）内存的申请和释放，由Matmul API内部实现管理。调用[接口内部管理CO1](#li135771283591)的Iterate函数原型后，调用[GetTensorC](get_tensor_c.md)接口完成L0C Buffer（CO1）上计算结果的搬出。
-   用户可以灵活自主地控制矩阵乘计算结果的搬运，例如将多次Iterate计算的矩阵乘结果缓存在L0C Buffer（CO1）内存中，在需要搬出该结果时，一次性搬出多块baseM \* baseN的C矩阵。这种灵活搬运场景下，用户需要提前申请L0C Buffer（CO1）的内存，调用[用户自主管理CO1](#li4843165185812)的Iterate函数原型后，一次Iterate的计算结果会输出到用户申请的L0C Buffer（CO1）内存上。在需要搬出计算结果时，调用[Fixpipe](../../../basic_api/cube_compute_isasi/cube_compute_store/fixpipe_l0_c_to_gm.md)接口搬运L0C Buffer（CO1）上的结果，完成后释放申请的L0C Buffer（CO1）内存。具体示例请参考[用户自主管理CO1的矩阵乘场景](matmul_usage.md#user-managed-co1)。

## 函数原型

-   <a name="li135771283591"></a>接口内部管理L0C Buffer（CO1）

    ```
    template <bool sync = true> __aicore__ inline bool Iterate(bool enPartialSum = false)
    ```

-   <a name="li4843165185812"></a>用户自主管理L0C Buffer（CO1）

    ```
    template <bool sync = true, typename T> __aicore__ inline bool Iterate(bool enPartialSum, const LocalTensor<T>& localCmatrix)
    ```

    
    -   Atlas 推理系列产品AI Core暂不支持用户自主管理L0C Buffer（CO1）。
    
    
    -   Atlas 200I/500 A2 推理产品暂不支持用户自主管理L0C Buffer（CO1）。
    

## 参数说明

**表1**  模板参数说明

| 参数名 | 描述 |
| --- | --- |
| sync | 迭代获取C矩阵分片的过程分为同步和异步两种模式。通过该参数设置同步或者异步模式：同步模式设置为true；异步模式设置为false。默认为同步模式。具体模式的介绍和使用方法请参考[GetTensorC](get_tensor_c.md)。 |
| T | 用户申请的L0C Buffer（CO1）内存上LocalTensor的数据类型，即矩阵乘输出的C矩阵的数据类型。当前支持的数据类型为float、int32_t。 |

**表2**  接口内部管理L0C Buffer（CO1）的函数参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| enPartialSum | 输入 | 是否将矩阵乘的结果累加于现有的L0C Buffer（CO1）数据，默认值为false。在L0C累加时，只支持C矩阵规格为singleCoreM==baseM && singleCoreN==baseN。 |

**表3**  用户自主管理L0C Buffer（CO1）的函数参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| enPartialSum | 输入 | 是否将矩阵乘的结果累加于现有的L0C Buffer（CO1）数据。在L0C累加时，只支持C矩阵规格为singleCoreM==baseM && singleCoreN==baseN。 |
| localCmatrix | 输出 | 由用户申请的L0C Buffer（CO1）上的LocalTensor内存，用于存放矩阵乘的计算结果。 |

## 返回值说明

false：单核上的所有数据全部算完。

true：数据仍在迭代计算中。

## 约束说明

-   当开启MixDualMaster（双主模式）场景时，即模板参数[enableMixDualMaster](matmul_config.md#matmulconfig-params)设置为true，不支持使用该接口。
-   对于用户自主管理CO1的Iterate函数，创建Matmul对象时，必须定义C矩阵的内存逻辑位置为TPosition::CO1、数据排布格式为CubeFormat::NZ、数据类型为float或int32\_t。

## 调用示例

同步模式及异步模式的简单调用示例如下。

```
// 同步模式样例
while (mm.Iterate()) {
    mm.GetTensorC(ubCmatrix);
}

// 异步模式样例
mm.template Iterate<false>();
// …… ……其它计算
for (int i = 0; i < singleM/baseM*singleN/baseN; ++i) {
    mm.template GetTensorC<false>(ubCmatrix);
}
```


<!-- cannbot:related:start -->
## 相关

- [启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖](../../../../../guides/operator_practice/simd_operator_optimization/pipeline_scheduling/enable_iterate_avoid_sync.md)（`explains`）：【描述】在MIX场景，即AIC（AI Cube核）和AIV（AI Vector核）混合编程中，调用Matmul Iterate或者IterateAll时，AIV发送消息到AIC启动Matmul计算。若通过Iterate同步方式，如图1同步方式消息发送示意图，每次调用都会触发一次消息发送，而通过Iterate异步方式，如异步方式消息发送示意图，仅第一次需要发送消息，后续无需发送消息，从而减少Cube与Vector核间交互，减少核间通信开销。因此，MIX场景推荐使用Iterate或者IterateAll异步接口（注意：使用异步接口时需要设置Workspace）。；- sync：迭代获取C矩阵分片的过程分为同步和异步两种模式。通过该参数设置同步或者异步模式：同步模式设置为true；异步模式设置为false。默认为同步模式。具体模式的介绍和使用方法请参考GetTensorC。。Guide 给出 MIX 中选择异步 Iterate 的通信原因与 workspace 前提，API 卡给出将 sync 设为 false 的具体入口。
- [IterateNBatch](iterate_n_batch.md)（`related`）：“每调用一次Iterate，会计算出一块baseM * baseN的C矩阵。接口内部会维护迭代进度，调用一次后会对A、B矩阵首地址进行偏移。”与“调用一次IterateNBatch，会进行N次IterateBatch计算，计算出N个多Batch的singleCoreM * singleCoreN大小的C矩阵。在调用该接口前，需将MatmulConfig中的isNBatch参数设为true，开启多Batch输入多Batch输出功能，并调用SetWorkspace接口申请临时空间，用于缓存计算结果，即IterateNBatch的结果输出至SetWorkspace指定的Global Memory内存中。”分别来自双方当前正文。Iterate 给出单次分块矩阵乘及内部进度推进，IterateNBatch 则把同一迭代模型扩展为多 Batch，并增加 isNBatch 与 SetWorkspace 前置合同；对照两卡可决定单块或批量执行路径。

<!-- cannbot:api-operator:start -->
### 知识正文中的调用示例

展示 3 / 3 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [QuantMatmul 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/quant_matmul_950.md)（`related`）：算子正文包含对 `Iterate(...)` 的直接调用；本卡提供该接口契约。
- [RotaryPositionEmbedding A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/posembedding/rotary_position_embedding.md)（`related`）：算子正文包含对 `Iterate(...)` 的直接调用；本卡提供该接口契约。
- [TransposeQuantBatchMatMulWeightNz 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/transpose_quant_batch_mat_mul_weight_nz_950.md)（`related`）：算子正文包含对 `Iterate(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
