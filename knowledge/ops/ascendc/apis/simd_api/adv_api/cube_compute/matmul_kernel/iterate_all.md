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
