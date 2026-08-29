---
type: API
title: GetPhyAddr
description: 返回LocalTensor的地址或指定偏移量后的地址。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/GetPhyAddr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetPhyAddr

返回LocalTensor的地址或指定偏移量后的地址。

返回LocalTensor的地址或指定偏移量后的地址。

本接口属于 LocalTensor 数据结构操作接口，用于访问和修改 UB 上的 Tensor 属性。

返回值：LocalTensor的地址或指定偏移量后的地址。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

<!-- cannbot:related:start -->
## 相关

- [Gather 双加 LocalTensor 基址导致交错旋转乱码](../../../../../runbooks/precision/localtensor_gather_base_address_not_double_counted.md)（`exemplifies`）：LocalTensor 参数已经确定了源数据的 UB 基址；该重载的有效寻址可按 `src.LocalBase + srcBaseAddr + offsets［i］` 理解。；返回LocalTensor的地址或指定偏移量后的地址。。故障卡的重复基址问题由 GetPhyAddr 返回 LocalTensor 基址的契约直接解释。
- [__aicore__ 禁止 void* 转 __ubuf__ 桥接](../../../../../runbooks/compilation/aicore_void_ubuf.md)（`exemplifies`）：边界与回退：void* 桥接路线 banned，整体回退；改让 wrapper 直接以 `const AscendC::LocalTensor<T>&` 形参接收队列出队的 tensor（dst、x 共用 T；mask 用独立固定类型 `const AscendC::LocalTensor<float>&`），在 wrapper 内部 `GetPhyAddr()` 取 `__ubuf__` 指针——地址空间转换由 LocalTensor 封装负责，不暴露 `void*` 中转。该路线编译推进到下一处错误，证明 void* 根因被消除。；返回LocalTensor的地址或指定偏移量后的地址。。Runbook的修法直接依赖 LocalTensor::GetPhyAddr 保留 UB 地址空间类型，API 卡给出该地址获取合同。
<!-- cannbot:related:end -->
