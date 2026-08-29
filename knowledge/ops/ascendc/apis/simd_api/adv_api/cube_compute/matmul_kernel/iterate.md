---
type: API
title: Iterate
description: 每调用一次计算一块baseM*baseN的C矩阵，内部维护迭代进度并偏移A、B矩阵首地址。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/Iterate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# Iterate

每调用一次Iterate，会计算出一块baseM * baseN的C矩阵。接口内部会维护迭代进度，调用一次后会对A、B矩阵首地址进行偏移。默认以先M轴再N轴的迭代顺序，也可以通过调整tiling参数iterateOrder，转换为先N轴再M轴的迭代顺序。当传入数据未对齐，存在尾块时，会在最后一次迭代输出尾块的计算结果。 一次Iterate矩阵乘的结果C矩阵存放在L0C Buffer（CO1）中，对于L0C Buffer（CO1）中计算结果的获取，当前支持如下两种方式： - 用户无需自行管理存放矩阵乘结果的L0C Buffer（CO1）内存的申请和释放，由Matmul API内部实现管理。

函数原型：
template <bool sync = true> __aicore__ inline bool Iterate(bool enPartialSum = false)
template <bool sync = true, typename T> __aicore__ inline bool Iterate(bool enPartialSum, const LocalTensor<T>& localCmatrix)

参数：
- sync：迭代获取C矩阵分片的过程分为同步和异步两种模式。通过该参数设置同步或者异步模式：同步模式设置为true；异步模式设置为false。默认为同步模式。具体模式的介绍和使用方法请参考GetTensorC。
- T：用户申请的L0C Buffer（CO1）内存上LocalTensor的数据类型，即矩阵乘输出的C矩阵的数据类型。当前支持的数据类型为float、int32_t。
- enPartialSum（输入）：是否将矩阵乘的结果累加于现有的L0C Buffer（CO1）数据，默认值为false。在L0C累加时，只支持C矩阵规格为singleCoreM==baseM && singleCoreN==baseN。
- enPartialSum（输入）：是否将矩阵乘的结果累加于现有的L0C Buffer（CO1）数据。在L0C累加时，只支持C矩阵规格为singleCoreM==baseM && singleCoreN==baseN。
- localCmatrix（输出）：由用户申请的L0C Buffer（CO1）上的LocalTensor内存，用于存放矩阵乘的计算结果。

返回值：false：单核上的所有数据全部算完。

约束：
- 当开启MixDualMaster（双主模式）场景时，即模板参数enableMixDualMaster设置为true，不支持使用该接口。
- 对于用户自主管理CO1的Iterate函数，创建Matmul对象时，必须定义C矩阵的内存逻辑位置为TPosition::CO1、数据排布格式为CubeFormat::NZ、数据类型为float或int32_t。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Kirin X90、Kirin 9030。不支持：Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖](../../../../../guides/operator_practice/simd_operator_optimization/pipeline_scheduling/enable_iterate_avoid_sync.md)（`explains`）：【描述】在MIX场景，即AIC（AI Cube核）和AIV（AI Vector核）混合编程中，调用Matmul Iterate或者IterateAll时，AIV发送消息到AIC启动Matmul计算。若通过Iterate同步方式，如图1同步方式消息发送示意图，每次调用都会触发一次消息发送，而通过Iterate异步方式，如异步方式消息发送示意图，仅第一次需要发送消息，后续无需发送消息，从而减少Cube与Vector核间交互，减少核间通信开销。因此，MIX场景推荐使用Iterate或者IterateAll异步接口（注意：使用异步接口时需要设置Workspace）。；- sync：迭代获取C矩阵分片的过程分为同步和异步两种模式。通过该参数设置同步或者异步模式：同步模式设置为true；异步模式设置为false。默认为同步模式。具体模式的介绍和使用方法请参考GetTensorC。。Guide 给出 MIX 中选择异步 Iterate 的通信原因与 workspace 前提，API 卡给出将 sync 设为 false 的具体入口。
- [IterateNBatch](iterate_n_batch.md)（`related`）：“每调用一次Iterate，会计算出一块baseM * baseN的C矩阵。接口内部会维护迭代进度，调用一次后会对A、B矩阵首地址进行偏移。”与“调用一次IterateNBatch，会进行N次IterateBatch计算，计算出N个多Batch的singleCoreM * singleCoreN大小的C矩阵。在调用该接口前，需将MatmulConfig中的isNBatch参数设为true，开启多Batch输入多Batch输出功能，并调用SetWorkspace接口申请临时空间，用于缓存计算结果，即IterateNBatch的结果输出至SetWorkspace指定的Global Memory内存中。”分别来自双方当前正文。Iterate 给出单次分块矩阵乘及内部进度推进，IterateNBatch 则把同一迭代模型扩展为多 Batch，并增加 isNBatch 与 SetWorkspace 前置合同；对照两卡可决定单块或批量执行路径。
<!-- cannbot:related:end -->
