---
type: API
title: GetPhyAddr
description: GlobalTensor::GetPhyAddr 接口，用于获取全局数据的物理地址，支持全平台。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/GetPhyAddr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetPhyAddr

GlobalTensor::GetPhyAddr 接口，用于获取全局数据的物理地址，支持全平台。

获取全局数据的地址。

本接口属于 GlobalTensor 数据结构操作接口，用于访问和修改 GM 上的 Tensor 属性。

返回值：全局数据的地址。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

<!-- cannbot:related:start -->
## 相关

- [GetPhyAddr const __gm__ 返回不可去 const](../../../../../runbooks/compilation/getphyaddr_const_gm_const.md)（`exemplifies`）：`AscendC::GlobalTensor<T>::GetPhyAddr()` 的返回类型是 `const __gm__ PrimType*`。C++ 规则下 `reinterpret_cast` 不能 casts away qualifiers（去 const），bisheng 编译器据此拒绝把 `const __gm__ int *` 转成 `__gm__ uint8_t *`。；GlobalTensor::GetPhyAddr 接口，用于获取全局数据的物理地址，支持全平台。；Runbook 用真实编译错误复现 GetPhyAddr 返回地址的 const 限定，并给出从 GM_ADDR 捕获可写裸指针的修复，直接示范该 API 合同的排障。
- [aicore 禁止 const char* cast 到 __gm__ T*](../../../../../runbooks/compilation/aicore_const_char_cast_gm_t.md)（`exemplifies`）：在 aicore kernel 中访问 GM 时，始终从 `__gm__` 限定的来源（`GM_ADDR` 入参、`GlobalTensor<T>::GetPhyAddr()`）派生指针，不要用 `reinterpret_cast` 把非 `__gm__` 指针升级为 `__gm__ T*`。；GlobalTensor::GetPhyAddr 接口，用于获取全局数据的物理地址，支持全平台。。Runbook要求从 `GlobalTensor<T>::GetPhyAddr()` 派生合法 GM 指针，API 卡定义获取该全局数据物理地址的接口。
<!-- cannbot:related:end -->
