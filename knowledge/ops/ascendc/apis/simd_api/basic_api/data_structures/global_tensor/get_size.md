---
type: API
title: GetSize
description: 获取GlobalTensor的元素个数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/GetSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetSize

获取GlobalTensor的元素个数。

传入全局数据地址，初始化GlobalTensor。

本接口组包含 SetGlobalBuffer。

本接口属于 GlobalTensor 数据结构操作接口，用于访问和修改 GM 上的 Tensor 属性。

返回值：无。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [UDMA GET size=0 污染后续 GET 致精度失败](../../../../../runbooks/precision/udma_get_size_zero_pollutes_engine_guard.md)（`exemplifies`）：GetSize 返回逻辑 tensor 长度，可在提交 UDMA 前做零长度 guard。
- [GetSize](../local_tensor/get_size.md)（`related`）：GlobalTensor 也暴露元素个数查询，可在 GM/Local 搬运两端核对 element count，但其存储域和初始化方式不同。
<!-- cannbot:related:end -->
