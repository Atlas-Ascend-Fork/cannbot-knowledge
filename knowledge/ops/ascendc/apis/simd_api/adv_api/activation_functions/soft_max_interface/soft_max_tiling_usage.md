---
type: API
title: SoftMax Tiling使用说明
description: Ascend C提供一组SoftMax Tiling API，方便用户获取SoftMax kernel计算时所需的Tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/SoftMax_interface/SoftMax_Tiling_usage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SoftMax Tiling使用说明

Ascend C提供一组SoftMax Tiling API，方便用户获取SoftMax kernel计算时所需的Tiling参数。 获取Tiling参数主要分为如下两步： 1. 获取SoftMax接口计算所需最小和最大临时空间大小，注意该步骤不是必须的，只是作为一个参考，供合理分配计算空间。 2. 获取输入SoftMax kernel侧接口所需tiling参数，需要传入AscendC::TensorShape类型的输入shape、剩余的可供softmax接口计算的空间大小和计算的数据类型大小。 SoftMax Tiling结构体的定义如下，开发者无需关注该tiling结构的具体信息，只需要传递到kernel侧，传入SoftMax高阶API接口，直接进行使用即可。

<!-- cannbot:related:start -->
## 相关

- [算子与高阶API共享临时Buffer](../../../../../guides/operator_practice/simd_operator_optimization/memory_access/shared_temp_buffer.md)（`explains`）：指南通过 SoftMax 与 Add 共享 UB 临时空间把单次搬运容量从 32KB 提到 64KB、搬运次数从 16 次降到 8 次；SoftMax Tiling 使用说明给出先查询最小/最大临时空间、再以剩余可用空间生成 tiling 的具体接口契约。
- [SoftmaxFlash Tiling接口](softmax_flash_tiling_interface.md)（`related`）：使用说明给出了先估算临时空间、再生成并传递 tiling 结构的完整 Host→Kernel 流程，补足单接口卡缺失的调用顺序。
- [SoftmaxFlashV2](softmax_flash_v2.md)（`related`）：《SoftmaxFlashV2》处理“SoftmaxFlash增强版本，对应FlashAttention-2算法，支持通过isUpdate参数控制是否根据前一次的sum和max更新当前结果，支持ND和NZ格式。”。《SoftMax Tiling使用说明》提供“Ascend C提供一组SoftMax Tiling API，方便用户获取SoftMax kernel计算时所需的Tiling参数。”，其具体合同或探针直接接入Flash softmax 的 update 状态、专用 Tiling 与在线 mi/li 依赖。
- [IsBasicBlockInSoftMax](is_basic_block_in_soft_max.md)（`same_topic`）：《SoftMax Tiling使用说明》处理“Ascend C提供一组SoftMax Tiling API，方便用户获取SoftMax kernel计算时所需的Tiling参数。”。《IsBasicBlockInSoftMax》明确提供“用于判断SoftMaxTiling结构是否符合基本块特征。”，其参数、调用或验证步骤直接接入SoftMax 的 Tiling 结构、临时空间、跨 VL 归约和 Kernel 参数合同。
- [SimpleSoftMax](simple_soft_max.md)（`same_topic`）：《SoftMax Tiling使用说明》处理“Ascend C提供一组SoftMax Tiling API，方便用户获取SoftMax kernel计算时所需的Tiling参数。”。《SimpleSoftMax》明确提供“使用预先计算好的sum和max数据对输入tensor按行做Softmax计算，内部不含reduce过程。”，其参数、调用或验证步骤直接接入SoftMax 的 Tiling 结构、临时空间、跨 VL 归约和 Kernel 参数合同。
- [SoftMax](soft_max.md)（`same_topic`）：《SoftMax Tiling使用说明》处理“Ascend C提供一组SoftMax Tiling API，方便用户获取SoftMax kernel计算时所需的Tiling参数。”。《SoftMax》明确提供“对输入tensor按行做Softmax计算，内部包含reducemax、exp、reducesum和div过程，可输出sum和max中间结果，支持ND和NZ格式。”，其参数、调用或验证步骤直接接入SoftMax 的 Tiling 结构、临时空间、跨 VL 归约和 Kernel 参数合同。
- [SoftMax/SimpleSoftMax Tiling](soft_max_simple_soft_max_tiling.md)（`same_topic`）：《SoftMax Tiling使用说明》处理“Ascend C提供一组SoftMax Tiling API，方便用户获取SoftMax kernel计算时所需的Tiling参数。”。《SoftMax/SimpleSoftMax Tiling》明确提供“用于获取SoftMax/SimpleSoftMax Tiling参数。”，其参数、调用或验证步骤直接接入SoftMax 的 Tiling 结构、临时空间、跨 VL 归约和 Kernel 参数合同。
- [SoftMax接口](soft_max_interface.md)（`same_topic`）：《SoftMax Tiling使用说明》处理“Ascend C提供一组SoftMax Tiling API，方便用户获取SoftMax kernel计算时所需的Tiling参数。”。《SoftMax接口》明确提供“提供SoftMax及其变体接口，包含SoftMax、SimpleSoftMax、SoftmaxFlash、SoftmaxGrad等以及Tiling使用说明。”，其参数、调用或验证步骤直接接入SoftMax 的 Tiling 结构、临时空间、跨 VL 归约和 Kernel 参数合同。
- [SoftmaxGrad Tiling接口](softmax_grad_tiling_interface.md)（`same_topic`）：SoftmaxGrad Tiling接口 与《SoftMax Tiling使用说明》的实质衔接是：SoftmaxGrad tiling 直接驱动反向 kernel，并与 forward/adjust/basic-block、rank 校验和 tiling 默认项配套。
<!-- cannbot:related:end -->
