---
type: API
title: Squeeze
description: 删除Layout的Shape中大小为1的指定维度并同步删除Stride中的对应维度，支持Tensor输入。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/Squeeze.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Squeeze

删除 Layout 的 Shape 中大小为 1 的指定维度，并同步删除 Stride 中的对应维度，支持 Layout 与 Tensor 输入。头文件为 tensor_api/tensor.h。
提供两种指定待删除维度的方式：通过模板参数 SqueezeDims 指定 Shape 顶层维度索引；或通过与 Shape 结构相同的 Pattern 指定，Pattern 中 _1 标记删除维度、_ 标记保留维度。
输入为 Tensor 时接口更新 Tensor 的 Layout，Engine、存储位置和数据起始地址保持不变；返回对象保留原 Layout 携带的 LayoutPattern 和 LayoutTrait 信息。
约束：SqueezeDims 至少包含一个顶层维度索引；编译期常量维度只有大小为 1 的才会被删除；运行时维度不校验，用户需自行保证大小为 1。
仅 Ascend 950PR/950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Select（基础API）](select.md)（`related`）：Squeeze 只允许删除大小为 1 的维度且保留 Tensor 存储，Select 则按编译期索引任意保留 Shape/Stride 子维；二者提供维度重写时的约束化选择。
- [AscUnsqueeze](../../../c_api/reg/data_compress/asc_unsqueeze.md)（`same_topic`）：AscUnsqueeze 与《Squeeze》的实质衔接是：AscUnsqueeze 按 mask 逆展开压缩数据，Unsqueeze 是对应基础入口，Squeeze/AscSqueeze 是生成压缩流和 mask 的逆向前置操作。
- [Squeeze](../../reg_vector_compute/compare_and_select/squeeze.md)（`same_topic`）：Squeeze：Squeeze 按 mask 压紧有效 lane，并通过 AR 字节数驱动非对齐 Store；C API、废弃替代链和 StoreUnAlign 正好覆盖同一压紧/搬出契约。 目标卡《Squeeze》补充：删除Layout的Shape中大小为1的指定维度并同步删除Stride中的对应维度，支持Tensor输入。
<!-- cannbot:related:end -->
