---
type: API
title: TILING_KEY_LIST
description: TILING_KEY_LIST函数用于在核函数中判断当前执行的TilingKey是否与Host侧配置的指定TilingKey匹配，从而标识满足TilingKey
  == key1或TilingKey == key2条件的分支逻辑。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.tiling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/TILING_KEY_LIST.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TILING_KEY_LIST

TILING_KEY_LIST函数用于在核函数中判断当前执行的TilingKey是否与Host侧配置的指定TilingKey匹配，从而标识满足TilingKey

TILING_KEY_LIST函数用于在核函数中判断当前执行的TilingKey是否与Host侧配置的指定TilingKey匹配，从而标识满足TilingKey == key1或TilingKey == key2条件的分支逻辑。

本接口属于 Kernel 侧 Tiling 接口，用于 Host 侧向 Kernel 侧传递 Tiling 参数。

约束：TILING_KEY_LIST运用于if和else if分支，不支持else分支，即用TILING_KEY_LIST函数来表征N个分支，必须用N个TILING_KEY_LIST(key1,key2)来分别表示。；支持传入两个TilingKey，每个TilingKey具备唯一性。；使用该接口时，必须设置默认的Kernel类型，也可以为某个TilingKey单独配置Kernel类型，该配置会覆盖默认Kernel类型。Kernel类型仅支持配置为KERNEL_TYPE_MIX_AIC_1_1、KERNEL_TYPE_MIX_AIC_1_2。；暂不支持Kernel直调工程。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。
