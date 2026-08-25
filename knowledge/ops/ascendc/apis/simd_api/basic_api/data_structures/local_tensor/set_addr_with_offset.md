---
type: API
title: SetAddrWithOffset
description: 设置带有偏移的Tensor地址。用于快速获取定义一个Tensor，同时指定新Tensor相对于旧Tensor首地址的偏移。偏移的长度为旧Tensor的元素个数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/SetAddrWithOffset.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetAddrWithOffset

设置带有偏移的 Tensor 地址，用于快速定义一个新 Tensor 并指定其相对于旧 Tensor 首地址的偏移，偏移单位为旧 Tensor 的元素个数。
函数签名为 template <typename S> void SetAddrWithOffset(LocalTensor<S>& src, uint32_t offset)，参数 src 为基础地址 Tensor，offset 为偏移长度。
常用于在同一缓冲区内复用空间，例如将 half 类型 Tensor 偏移到 float 类型 Tensor 的后半段空间。
无返回值，直接修改调用方 Tensor 的地址指针。
支持 Ascend 950PR/950DT、Atlas A2、Atlas A3、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品 AI Core 与 Vector Core 以及 Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [DataCopy 不自动按 tile 推进须显式元素 offset](../../../../../runbooks/precision/datacopy_setglobalbuffer_no_auto_advance_tileoffset.md)（`exemplifies`）：SetAddrWithOffset 与《DataCopy 不自动按 tile 推进须显式元素 offset》的实质衔接是：SetAddrWithOffset 与子视图/偏移接口共享元素偏移契约，所选故障卡直接说明错误基址叠加、L1/L0 限制及 DataCopy 偏移修复。
- [DataCopyPad 五参编译失败—LocalTensor 子视图替代偏移](../../../../../runbooks/compilation/datacopypad_offset_via_tensor_subview.md)（`exemplifies`）：该 API 给出以元素 offset 建立 LocalTensor 地址视图的正式接口，可作为 focal 中 operator[] 子视图方案的显式地址偏移替代，并提醒 offset 单位是元素而非字节。
- [Gather 双加 LocalTensor 基址导致交错旋转乱码](../../../../../runbooks/precision/localtensor_gather_base_address_not_double_counted.md)（`exemplifies`）：《Gather 双加 LocalTensor 基址导致交错旋转乱码》处理“Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。”。《SetAddrWithOffset》明确提供“设置带有偏移的Tensor地址。用于快速获取定义一个Tensor，同时指定新Tensor相对于旧Tensor首地址的偏移。偏移的长度为旧Tensor的元素个数。”，其参数、调用或验证步骤直接接入Gather 的 base 地址、byte offset、重复偏移故障和地址计算合同。
- [L1/L0 tensor 须用 TPosition 构造非 SetAddr](../../../../../runbooks/compilation/l1_l0_tensor_tposition_setaddr.md)（`exemplifies`）：SetAddrWithOffset 与《L1/L0 tensor 须用 TPosition 构造非 SetAddr》的实质衔接是：SetAddrWithOffset 与子视图/偏移接口共享元素偏移契约，所选故障卡直接说明错误基址叠加、L1/L0 限制及 DataCopy 偏移修复。
- [GetWithOffset](../../resource_management/t_buf/get_with_offset.md)（`related`）：SetAddrWithOffset 与《GetWithOffset》的实质衔接是：SetAddrWithOffset 与子视图/偏移接口共享元素偏移契约，所选故障卡直接说明错误基址叠加、L1/L0 限制及 DataCopy 偏移修复。
- [OperatorSubscript](operator.md)（`same_topic`）：SetAddrWithOffset 与《OperatorSubscript》的实质衔接是：SetAddrWithOffset 与子视图/偏移接口共享元素偏移契约，所选故障卡直接说明错误基址叠加、L1/L0 限制及 DataCopy 偏移修复。
<!-- cannbot:related:end -->
