---
type: API
title: PhiloxRandom
description: 基于Philox随机数生成算法，给定随机数种子，生成若干的随机数。 Philox随机数生成的核心算法是一个基于记数的伪随机数生成算法，输入为一个128bit的记数器C，两个32bit的key（k0和k1），输出为4个32bit的整数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.random_sampling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/random_functions/PhiloxRandom.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# PhiloxRandom

基于Philox算法生成随机数，支持生成half/float/int32_t类型的随机数。通过seed和subsequence初始化随机数生成器，可在counter基础上生成指定数量的随机数。

函数原型提供通过sharedTmpBuffer传入临时空间和接口框架申请两种方式。接口参数包含dstTensor输出随机数Tensor、sharedTmpBuffer临时缓存、PhiloxRandomState随机数生成器状态（含seed、subsequence、counter等信息）、calCount生成元素个数。

约束：遵循通用地址对齐约束。
