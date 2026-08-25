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
