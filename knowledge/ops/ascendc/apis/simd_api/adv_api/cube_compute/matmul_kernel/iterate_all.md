---
type: API
title: IterateAll
description: 调用一次IterateAll，会计算出singleCoreM \ singleCoreN大小的C矩阵。迭代顺序可通过tiling参数iterateOrder调整。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/IterateAll.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# IterateAll

调用一次IterateAll，会计算出singleCoreM * singleCoreN大小的C矩阵。迭代顺序可通过tiling参数iterateOrder调整。

函数原型：
template <bool sync = true> __aicore__ inline void IterateAll(const GlobalTensor<DstT>& gm, uint8_t enAtomic = 0, bool enSequentialWrite = false, bool waitIterateAll = false, bool fakeMsg = false)
template <bool sync = true> __aicore__ inline void IterateAll(const LocalTensor<DstT>& ubCmatrix, uint8_t enAtomic = 0)

参数：
- sync：获取C矩阵过程分为同步和异步两种模式：同步：需要同步等待IterateAll执行结束。 异步：不需要同步等待IterateAll执行结束。 通过该参数设置同步或者异步模式：同步模式设置为true；异步模式设置为false，默认为同步模式。
- gm（输出）：C矩阵。类型为GlobalTensor。不同型号支持的数据类型请参考支持的数据类型。
- ubCmatrix（输出）：C矩阵。类型为LocalTensor，支持的TPosition为TSCM、VECIN，输出到VECIN Tensor时建议使用Iterate接口。不同型号支持的数据类型请参考支持的数据类型。
- enAtomic（输入）：是否开启Atomic操作，默认值为0。 参数取值： 0：不开启Atomic操作 1：开启AtomicAdd累加操作 2：开启AtomicMax求最大值操作 3：开启AtomicMin求最小值操作
- enSequentialWrite（输入）：是否开启连续写模式（连续写，写入[baseM, baseN]；非连续写，写入[singleCoreM, singleCoreN]中对应的位置），默认值false（非连续写模式）。不支持该参数。

约束：
- 传入的C矩阵地址空间大小需要保证不小于singleCoreM * singleCoreN个元素。
- 支持的数据类型：Ascend 950PR/Ascend 950DT 支持 half、float、bfloat16_t、int32_t、int8_t、fp8_e4m3fn_t 和 hifloat8_t；Atlas A3/A2 系列支持 half、float、bfloat16_t、int32_t 和 int8_t。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Kirin X90。不支持：Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Matmul workspace 预偏移 totalN 回读 banned](../../../../../runbooks/precision/matmul_workspace_totaln_banned.md)（`exemplifies`）：Runbook 的核心错误是按 totalN 预留/偏移输出，而 IterateAll 明确一次只写 singleCoreM×singleCoreN；该输出契约直接决定 workspace 步长。
- [Matmul高阶API开启IBShare模板共享B矩阵数据](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_ibshare_b.md)（`explains`）：《IterateAll》说明调用一次IterateAll，会计算出singleCoreM \ singleCoreN大小的C矩阵。迭代顺序可通过tiling参数iterateOrder调整。；《Matmul高阶API开启IBShare模板共享B矩阵数据》说明本案例呈现了在矩阵乘算子场景中，使用Matmul高阶API进行矩阵乘法计算，B矩阵开启IBShare对算子性能的提升效果。IBShare功能通过共享L1 Buffer上相同的A矩阵或B矩阵数据，减少重复的MTE2数据搬运开销，提升算子性能。该功能支持A矩阵和B矩阵其中一个矩阵开启IBShare，也支持A矩阵和B矩阵同时开启IBShare。。二者在IterateAll一次完成singleCoreM×singleCoreN，异步模式必须配WaitIterateAll并按GetTensorC/输出场景消费结果上存在可执行的直接衔接。
- [Matmul高阶API开启NBuffer33模板](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_nbuffer33.md)（`explains`）：《IterateAll》说明调用一次IterateAll，会计算出singleCoreM \ singleCoreN大小的C矩阵。迭代顺序可通过tiling参数iterateOrder调整。；《Matmul高阶API开启NBuffer33模板》说明MTE2 Bound场景下开启NBuffer33模板，将A矩阵切分为3x3基本块错开搬运流水，平衡MTE2与FixPipe数据流量。。二者在IterateAll一次完成singleCoreM×singleCoreN，异步模式必须配WaitIterateAll并按GetTensorC/输出场景消费结果上存在可执行的直接衔接。
- [启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖](../../../../../guides/operator_practice/simd_operator_optimization/pipeline_scheduling/enable_iterate_avoid_sync.md)（`explains`）：《IterateAll》说明调用一次IterateAll，会计算出singleCoreM \ singleCoreN大小的C矩阵。迭代顺序可通过tiling参数iterateOrder调整。；《启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖》说明MIX场景下推荐使用Iterate或IterateAll异步接口，减少Cube与Vector核间消息交互，降低通信开销。。二者在IterateAll一次完成singleCoreM×singleCoreN，异步模式必须配WaitIterateAll并按GetTensorC/输出场景消费结果上存在可执行的直接衔接。
- [异步场景处理](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/async_scenario.md)（`explains`）：《IterateAll》说明调用一次IterateAll，会计算出singleCoreM \ singleCoreN大小的C矩阵。迭代顺序可通过tiling参数iterateOrder调整。；《异步场景处理》说明Matmul的Iterate和IterateAll接口在MIX场景（包含矩阵计算和矢量计算）下提供了同步和异步两种模式，纯Cube场景（只有矩阵计算）下，只支持同步模式。。二者在IterateAll一次完成singleCoreM×singleCoreN，异步模式必须配WaitIterateAll并按GetTensorC/输出场景消费结果上存在可执行的直接衔接。
- [算子实现](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/operator_impl.md)（`explains`）：《IterateAll》说明调用一次IterateAll，会计算出singleCoreM \ singleCoreN大小的C矩阵。迭代顺序可通过tiling参数iterateOrder调整。；《算子实现》说明介绍使用Matmul高阶API实现矩阵乘算子的流程，包括Host侧Tiling参数获取与Kernel侧矩阵乘操作。。二者在IterateAll一次完成singleCoreM×singleCoreN，异步模式必须配WaitIterateAll并按GetTensorC/输出场景消费结果上存在可执行的直接衔接。
- [GetTensorC](get_tensor_c.md)（`related`）：《IterateAll》说明调用一次IterateAll，会计算出singleCoreM \ singleCoreN大小的C矩阵。迭代顺序可通过tiling参数iterateOrder调整。；《GetTensorC》说明Iterate后获取C矩阵分片，可输出到GM或UB，支持同步与异步两种模式。。二者在IterateAll一次完成singleCoreM×singleCoreN，异步模式必须配WaitIterateAll并按GetTensorC/输出场景消费结果上存在可执行的直接衔接。
- [Iterate](iterate.md)（`related`）：《IterateAll》说明调用一次IterateAll，会计算出singleCoreM \ singleCoreN大小的C矩阵。迭代顺序可通过tiling参数iterateOrder调整。；《Iterate》说明每调用一次计算一块baseM*baseN的C矩阵，内部维护迭代进度并偏移A、B矩阵首地址。。二者在IterateAll一次完成singleCoreM×singleCoreN，异步模式必须配WaitIterateAll并按GetTensorC/输出场景消费结果上存在可执行的直接衔接。
- [IterateAll](../../convolution_compute/conv3_d_kernel/iterate_all.md)（`related`）：Matmul 同名接口异步/输出契约不同，不能直接套用。
- [Matmul Kernel侧接口](matmul_kernel.md)（`related`）：《IterateAll》说明调用一次IterateAll，会计算出singleCoreM \ singleCoreN大小的C矩阵。迭代顺序可通过tiling参数iterateOrder调整。；《Matmul Kernel侧接口》说明提供Matmul矩阵乘的Kernel侧接口，包含模板参数、配置类、Init、SetTensorA/B、Iterate等方法及使用说明。。二者在IterateAll一次完成singleCoreM×singleCoreN，异步模式必须配WaitIterateAll并按GetTensorC/输出场景消费结果上存在可执行的直接衔接。
- [Matmul使用说明](matmul_usage.md)（`related`）：《IterateAll》说明调用一次IterateAll，会计算出singleCoreM \ singleCoreN大小的C矩阵。迭代顺序可通过tiling参数iterateOrder调整。；《Matmul使用说明》说明Ascend C提供一组Matmul高阶API，方便用户快速实现Matmul矩阵乘法的运算操作。。二者在IterateAll一次完成singleCoreM×singleCoreN，异步模式必须配WaitIterateAll并按GetTensorC/输出场景消费结果上存在可执行的直接衔接。
- [WaitIterateAll](wait_iterate_all.md)（`same_topic`）：《IterateAll》说明调用一次IterateAll，会计算出singleCoreM \ singleCoreN大小的C矩阵。迭代顺序可通过tiling参数iterateOrder调整。；《WaitIterateAll》说明等待IterateAll异步接口返回，支持连续输出到Global Memory。。二者在IterateAll一次完成singleCoreM×singleCoreN，异步模式必须配WaitIterateAll并按GetTensorC/输出场景消费结果上存在可执行的直接衔接。
<!-- cannbot:related:end -->
