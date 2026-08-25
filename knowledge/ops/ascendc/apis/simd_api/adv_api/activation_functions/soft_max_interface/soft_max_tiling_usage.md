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
