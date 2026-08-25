---
type: API
title: ReinterpretCast
description: 将当前Tensor重解释为用户指定的新类型，转换后的Tensor与原Tensor地址及内容完全相同，Tensor的大小（字节数）保持不变。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/ReinterpretCast.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# ReinterpretCast

将当前Tensor重解释为用户指定的新类型，转换后的Tensor与原Tensor地址及内容完全相同，Tensor的大小（字节数）保持不变。

将当前Tensor重解释为用户指定的新类型，转换后的Tensor与原Tensor地址及内容完全相同，Tensor的大小（字节数）保持不变。

本接口属于 LocalTensor 数据结构操作接口，用于访问和修改 UB 上的 Tensor 属性。

返回值：重解释转换后的Tensor。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

<!-- cannbot:related:start -->
## 相关

- [FreeTensor早释使队列别名被下一轮DMA覆盖](../../../../../runbooks/precision/reinterpret_tensor_alias_must_outlive_queue_release.md)（`exemplifies`）：Runbook 验证 ReinterpretCast 产生的是共享底层存储别名，若原队列 Tensor FreeTensor 后复用 Buffer，别名会被下一轮 DMA 覆盖。
- [__ubuf__ 指针传普通形参导致编译失败](../../../../../runbooks/compilation/ubuf_pointer_preserves_address_space.md)（`exemplifies`）：__ubuf__ 指针传普通形参导致编译失败 与《ReinterpretCast》的实质衔接是：__ubuf__ 是指针类型的一部分，helper 形参、Load/Store、ReinterpretCast、地址空间转换与谓词必须保留相同 qualifier，不能隐式退化为普通 T*。
- [ReinterpretCast](../global_tensor/reinterpret_cast.md)（`related`）：LocalTensor 与 GlobalTensor 的 ReinterpretCast 都保持地址、字节数和内容不变，只改变元素类型解释；可按存储层级映射。
- [SetSize](set_size.md)（`related`）：重解释保持总字节数但元素宽度变化后，逻辑元素数可能需用 SetSize 调整，避免后续接口按旧长度访问。
<!-- cannbot:related:end -->
