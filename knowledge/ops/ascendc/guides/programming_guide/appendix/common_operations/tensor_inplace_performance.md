---
type: Guide
title: 如何使用Tensor原地操作提升算子性能
description: Tensor原地操作（inplace接口）是一种优化技术，全局申请、保留LocalTensor内存，避免了频繁创建和销毁LocalTensor对象。AllocTensor、FreeTensor、EnQue、DeQue接口不产生新的LocalTensor，而是在该全局LocalTensor上反复申请、释放、入队、出队。其实现原理如下图所示：
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/appendix/common_operations/tensor_inplace_performance.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 如何使用Tensor原地操作提升算子性能

Tensor原地操作（inplace接口）是一种优化技术，全局申请、保留LocalTensor内存，避免了频繁创建和销毁LocalTensor对象。AllocTensor、FreeTensor、EnQue、DeQue接口不产生新的LocalTensor，而是在该全局LocalTensor上反复申请、释放、入队、出队。其实现原理如下图所示：
## Tensor原地操作的优势
-   减少栈变换：相比构造新Tensor的方式，inplace接口减少了LocalTensor的栈变换，允许Tensor被反复使用。
-   减少入队/出队操作：在调用EnQue、DeQue的过程中，TQue对象没有存储该Tensor对应的Buffer地址，实际没有真正入队、出队，减少了反复入队、出队的Scalar指令。
## 保留EnQue和DeQue的原因
既然Tensor原地操作没有执行真正的入队出队操作，为什么还需要保留EnQue和DeQue接口呢？
-   编程兼容性：为了保持编程接口的一致性，inplace接口仍然需要调用EnQue和DeQue，确保代码结构的统一性和可维护性。
-   内存同步功能：EnQue和DeQue操作中实现了内存读写同步功能，确保数据的一致性和正确性，即使没有实际的队列操作，这些同步机制仍然需要保留。
## 适用场景
适合计算循环次数多的场景：如图1所示，inplace接口虽然增加了TQue对象InitBuffer的初始化开销，但显著减少了每次循环中AllocTensor、EnQue、DeQue和FreeTensor内部对LocalTensor和事件的操作次数，特别适合需要多次循环来完成计算的场景。
## 使用方法
- 配置TQue对象：在创建TQue对象时，设置深度（depth）为0，启用inplace操作模式。
- 调用原地操作接口：使用inplace接口直接操作LocalTensor。
- AllocTensor和DeQue区分non-inplace和inplace接口，详情请参考AllocTensor、DeQue。
- FreeTensor和EnQue不区分non-inplace和inplace接口。
## 示例代码

<!-- cannbot:related:start -->
## 相关

- [HardSwish 逐元素 kernel 的 TQue 双缓冲实现配方](../../../../runbooks/compilation/elementwise_tque_double_buffer_inplace_recipe.md)（`related`）：原地操作性能指南给出原则，该配方把原则落实为 elementwise kernel 的 TQue 双缓冲和安全 inplace 读写顺序。
- [TQue tensor 所有权只能 DeQue 一次](../../../../runbooks/compilation/tque_tensor_ownership_single_dequeue.md)（`related`）：Tensor inplace 复用若重复 DeQue 同一队列对象会破坏所有权；该卡给出一次 DeQue 后沿流水传递 Tensor 的约束。
<!-- cannbot:related:end -->
