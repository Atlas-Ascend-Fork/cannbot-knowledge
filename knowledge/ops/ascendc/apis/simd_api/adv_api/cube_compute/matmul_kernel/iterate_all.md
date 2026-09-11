---
type: API
title: IterateAll
description: 调用一次IterateAll，会计算出singleCoreM \ singleCoreN大小的C矩阵。迭代顺序可通过tiling参数iterateOrder调整。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.programming_model.execution_unit.cube
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/IterateAll.md
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

# IterateAll

## 功能说明

调用一次IterateAll，会计算出singleCoreM \* singleCoreN大小的C矩阵。迭代顺序可通过tiling参数iterateOrder调整。

## 函数原型

```
template <bool sync = true> __aicore__ inline void IterateAll(const GlobalTensor<DstT>& gm, uint8_t enAtomic = 0, bool enSequentialWrite = false, bool waitIterateAll = false, bool fakeMsg = false)
```

```
template <bool sync = true> __aicore__ inline void IterateAll(const LocalTensor<DstT>& ubCmatrix, uint8_t enAtomic = 0)
```

## 参数说明

**表1**  模板参数说明

| 参数名 | 描述 |
| --- | --- |
| sync | 获取C矩阵过程分为同步和异步两种模式：<br>同步：需要同步等待IterateAll执行结束。<br>异步：不需要同步等待IterateAll执行结束。<br><br>通过该参数设置同步或者异步模式：同步模式设置为true；异步模式设置为false，默认为同步模式。 |

**表2**  接口参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| gm | 输出 | C矩阵。类型为[GlobalTensor](../../../basic_api/data_structures/global_tensor/index.md)。不同型号支持的数据类型请参考[支持的数据类型](#li12616155731720)。 |
| ubCmatrix | 输出 | C矩阵。类型为[LocalTensor](../../../basic_api/data_structures/local_tensor/index.md)，支持的TPosition为TSCM、VECIN，输出到VECIN Tensor时建议使用[Iterate](iterate.md)接口。不同型号支持的数据类型请参考[支持的数据类型](#li12616155731720)。 |
| enAtomic | 输入 | 是否开启Atomic操作，默认值为0。<br><br>参数取值：<br><br>0：不开启Atomic操作<br><br>1：开启AtomicAdd累加操作<br><br>2：开启AtomicMax求最大值操作<br><br>3：开启AtomicMin求最小值操作 |
| enSequentialWrite | 输入 | 是否开启连续写模式（[连续写](get_tensor_c.md#fig580415103338)，写入[baseM, baseN]；[非连续写](get_tensor_c.md#fig322951853119)，写入[singleCoreM, singleCoreN]中对应的位置），默认值false（非连续写模式）。不支持该参数。 |
| waitIterateAll | 输入 | 仅在异步场景下使用，是否需要通过[WaitIterateAll](wait_iterate_all.md)接口等待IterateAll执行结束。<br><br>true：需要通过WaitIterateAll接口等待IterateAll执行结束。<br><br>false：不需要通过WaitIterateAll接口等待IterateAll执行结束，开发者自行处理等待IterateAll执行结束的过程。 |
| fakeMsg | 输入 | 仅在IBShare场景（模板参数中开启了[doIBShareNorm](matmul_config.md#matmulconfig-params)开关）和IntraBlockPartSum场景（模板参数中开启了[intraBlockPartSum](matmul_config.md#matmulconfig-params)开关）使用。<br>IBShare场景：<br>该场景复用L1上相同的A矩阵或B矩阵数据，要求AIV分核调用IterateAll的次数必须匹配，此时需要调用IterateAll并设置fakeMsg为true，不执行真正的计算，仅用来保证IterateAll调用成对出现。默认值为false，表示执行真正的计算。<br><br>IntraBlockPartSum场景：<br>用于分离模式下的Vector计算、Cube计算融合，实现多个AIV核的一次Matmul计算结果（baseM * baseN大小的矩阵分片）在L0C Buffer上累加。默认值为false，表示执行各AIV核的Matmul计算结果在L0C Buffer上累加。 |

## 返回值说明

无

## 约束说明

-   传入的C矩阵地址空间大小需要保证不小于singleCoreM \* singleCoreN个元素。

-   支持的数据类型<a id="li12616155731720"></a>

    
    Ascend 950PR/Ascend 950DT，支持的数据类型为：half、float、bfloat16_t、int32_t、int8_t、fp8_e4m3fn_t、hifloat8_t。
    

    
    Atlas A3 训练系列产品/Atlas A3 推理系列产品，支持的数据类型为：half、float、bfloat16_t、int32_t、int8_t。
    

    
    Atlas A2 训练系列产品/Atlas A2 推理系列产品，支持的数据类型为：half、float、bfloat16_t、int32_t、int8_t。
    

    
    Atlas 推理系列产品AI Core，不支持包含ubCmatrix参数的原型，对于包含gm参数的原型，支持的数据类型为：half、float、int8_t、int32_t。
    

    
    Atlas 200I/500 A2 推理产品，支持的数据类型为：half、float、bfloat16_t、int32_t。
    

    
    Kirin X90，支持的数据类型为：half、int8_t、int32_t。
    





## 调用示例

IterateAll接口的调用示例如下。

```
REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm, &tiling);
mm.SetTensorA(gm_a);
mm.SetTensorB(gm_b);
if (tiling.isBias) {
    mm.SetBias(gmBias);
}
mm.IterateAll(gm_c);    // 计算
mm.End();
```


<!-- cannbot:related:start -->
## 相关

- [Matmul workspace 预偏移 totalN 回读 banned](../../../../../runbooks/precision/matmul_workspace_totaln_banned.md)（`exemplifies`）：AIC `Matmul` 高阶 API 把 INT32 中间结果经 `IterateAll` 写入 GM workspace，AIV 从 workspace 读回做反量化；多核切分单核 M/N。；调用一次IterateAll，会计算出singleCoreM * singleCoreN大小的C矩阵。迭代顺序可通过tiling参数iterateOrder调整。。Runbook 的错误路线直接依赖 IterateAll 把每核 INT32 结果写入 GM workspace，再由 AIV 按布局回读；API 卡给出单次输出的 singleCoreM×singleCoreN 契约，正是判断预偏移和 totalN stride 是否成立的接口依据。
- [Matmul高阶API开启IBShare模板共享B矩阵数据](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_ibshare_b.md)（`explains`）：案例硬约束“A矩阵和B矩阵同时开启IBShare的场景，获取矩阵计算结果时，只支持调用IterateAll接口，且只支持输出到Global Memory。”；IterateAll API定义“调用一次IterateAll，会计算出singleCoreM * singleCoreN大小的C矩阵。”。API卡给出案例唯一允许的结果获取调用及输出尺寸合同。
- [启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖](../../../../../guides/operator_practice/simd_operator_optimization/pipeline_scheduling/enable_iterate_avoid_sync.md)（`explains`）：【描述】在MIX场景，即AIC（AI Cube核）和AIV（AI Vector核）混合编程中，调用Matmul Iterate或者IterateAll时，AIV发送消息到AIC启动Matmul计算。若通过Iterate同步方式，如图1同步方式消息发送示意图，每次调用都会触发一次消息发送，而通过Iterate异步方式，如异步方式消息发送示意图，仅第一次需要发送消息，后续无需发送消息，从而减少Cube与Vector核间交互，减少核间通信开销。因此，MIX场景推荐使用Iterate或者IterateAll异步接口（注意：使用异步接口时需要设置Workspace）。；- sync：获取C矩阵过程分为同步和异步两种模式：同步：需要同步等待IterateAll执行结束。 异步：不需要同步等待IterateAll执行结束。 通过该参数设置同步或者异步模式：同步模式设置为true；异步模式设置为false，默认为同步模式。。Guide 给出 MIX 中选择异步 IterateAll 的通信原因与 workspace 前提，API 卡给出将 sync 设为 false 的具体入口。
- [异步场景处理](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/async_scenario.md)（`explains`）：“获取C矩阵过程分为同步和异步两种模式”与“需要IterateAll的结果时，调用WaitIterateAll等待IterateAll异步接口返回”把接口参数选择落实为完整异步使用步骤。
- [WaitIterateAll](wait_iterate_all.md)（`related`）：异步：不需要同步等待IterateAll执行结束。；等待IterateAll异步接口返回，支持连续输出到Global Memory。。左卡允许 IterateAll 以 sync=false 发起异步矩阵计算，右卡负责等待该异步调用完成；两端给出发起与完成等待的直接生命周期顺序。

<!-- cannbot:api-operator:start -->
### 知识正文中的调用示例

展示 8 / 8 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [UpsampleBilinear2dAA A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bilinear_2d_aa.md)（`related`）：算子正文包含对 `IterateAll(...)` 的直接调用；本卡提供该接口契约。
- [TransposeBatchMatMul A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/transpose_batch_mat_mul.md)（`related`）：算子正文包含对 `IterateAll(...)` 的直接调用；本卡提供该接口契约。
- [grouped_matmul_add A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul_add.md)（`related`）：算子正文包含对 `IterateAll(...)` 的直接调用；本卡提供该接口契约。
- [UpsampleBilinear2dAABackward A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bilinear_2d_aa_backward.md)（`related`）：算子正文包含对 `IterateAll(...)` 的直接调用；本卡提供该接口契约。
- [WeightQuantBatchMatmulNz 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/weight_quant_batch_matmul_nz_950.md)（`related`）：算子正文包含对 `IterateAll(...)` 的直接调用；本卡提供该接口契约。
- [grouped_matmul_swiglu_quant A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul_swiglu_quant.md)（`related`）：算子正文包含对 `IterateAll(...)` 的直接调用；本卡提供该接口契约。
- [LSTM A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/rnn/lstm.md)（`related`）：算子正文包含对 `IterateAll(...)` 的直接调用；本卡提供该接口契约。
- [MhcPostBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mhc/mhc_post_backward_950.md)（`related`）：算子正文包含对 `IterateAll(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
