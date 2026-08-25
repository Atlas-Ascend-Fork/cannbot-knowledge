---
type: API
title: GetValue
description: 获取GlobalTensor的相应偏移位置的值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/GetValue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetValue

获取GlobalTensor的相应偏移位置的值。

如图1所示，在AI Core内部，Scalar单元和DMA单元都可能对GM进行访问： - DMA搬运单元读写GM，数据通过DataCopy等接口在UB等Local Memory和GM间交互，没有Cache一致性问题。 - Scalar单元访问GM，首先会访问每个核内的Data Cache，因此存在Data Cache与GM的Cache一致性问题。 图1 DataCache内存层次示意图 DataCacheCleanAndInvalid接口用于解决上述一致性问题，其功能可以拆解为两部分： - Clean：将缓存中被修改过的数据（脏数据，Dirty Data）写回到GM中，避免数据丢失。 - Invalid： - 将指定地址范围的Cache Line标记为“无效”，使其从缓存中移除。 - 保证下一次访问这些内存地址时，会从GM重新加载数据，而不是使用可能过期的缓存数据。 该接口的典型使用场景如

本接口组包含 DataCacheCleanAndInvalid。

本接口属于 GlobalTensor 数据结构操作接口，用于访问和修改 GM 上的 Tensor 属性。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
