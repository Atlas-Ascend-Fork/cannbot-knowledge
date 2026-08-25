---
type: API
title: TQue简介
description: 流水任务之间通过队列（Queue）完成任务间通信和同步。TQue是用来执行队列相关操作、管理相关资源的数据结构。TQue继承自TQueBind父类，继承关系如下：
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQue/TQue_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TQue简介

流水任务之间通过队列（Queue）完成任务间通信和同步。TQue是用来执行队列相关操作、管理相关资源的数据结构。TQue继承自TQueBind父类，继承关系如下：

本接口属于资源管理接口，用于管理 Queue、Buffer 等计算资源。

# TQue简介 流水任务之间通过队列（Queue）完成任务间通信和同步。TQue是用来执行队列相关操作、管理相关资源的数据结构。TQue继承自TQueBind父类，继承关系如下： ## 模板参数 表1 TQue模板参数介绍 参数名称 含义 pos 队列逻辑位置，可以为 VECIN、VECOUT、 A1 、 A2 、 B1 、 B2 、 CO1 、 CO2。 关于TPosition的具体介绍请参考 TPosition 。 depth 队列的深度表示该队列可以连续进行入队/出队的次数，在代码运行时，对同一个队列有n次连续的EnQue（中间没有DeQue），那么该队列的深度就需要设置为n。 注意，这里的队列深度和double buffer无关，队列机制用于实现流水线并行，double buffer在此基础上进一步提高流水线的利用率。即使队列的深度为1，仍可以开启double buffer。 非Tensor原地操作的场景下，队列的深度设置为1时，编译器对这种场景做了特殊优化，性能通常更好， 推荐设置为1 。 Tensor原地操作 的场景下，需要设置为0。 如下样例中队列没有连续入队，队列的深

<!-- cannbot:related:start -->
## 相关

- [ACL 507035 — 空 TQue DeQue 触发 B16 路径异常](../../../../../runbooks/compilation/tque_dequeue_requires_prior_enqueue_507035.md)（`exemplifies`）：ACL 507035 — 空 TQue DeQue 触发 B16 路径异常 与《TQue简介》的实质衔接是：空队列 DeQue 违反 AllocTensor→EnQue→DeQue→FreeTensor 的所有权链；相关失败卡覆盖重复 DeQue、早释、未释放、InitBuffer 参数和验证报错，Sin/Cos 是该 B16 分支中实际触发计算。
- [TQue tensor 所有权只能 DeQue 一次](../../../../../runbooks/compilation/tque_tensor_ownership_single_dequeue.md)（`exemplifies`）：TQue tensor 所有权只能 DeQue 一次 与《TQue简介》的实质衔接是：TQue 元素必须严格 Alloc→EnQue→DeQue→Free 且只由一个消费者出队；相关 API、生命周期指南和失败卡覆盖临时值、早释、空队列及跨函数交接。
- [TQueBind简介](../t_que_bind/t_que_bind_intro.md)（`same_topic`）：TQueBind简介 与《TQue简介》的实质衔接是：TQueBind 与 TQue 的差别在绑定两队列；复用、EnQue 重载和 InitBuffer 故障卡直接约束该资源生命周期。
<!-- cannbot:related:end -->
