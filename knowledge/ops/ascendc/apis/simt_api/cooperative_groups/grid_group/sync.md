---
type: API
title: Grid协作组sync
description: 同步当前Grid内所有SIMT线程。所有线程块中的所有线程都执行到该同步点位置后，Grid内线程才能继续执行。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/grid_group/sync.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# Grid协作组sync

同步当前Grid内所有SIMT线程。所有线程块中的所有线程都执行到该同步点位置后，Grid内线程才能继续执行。
函数原型：void sync() const
约束：仅支持SIMT编程场景，不支持SIMD与SIMT混合编程场景。；必须保证Grid内所有线程都能执行到同一个sync()调用，否则是未定义行为。；确保Grid中的线程块总数不超过设备的AIV物理核数，以避免程序卡死。开发者可以通过《Runtime运行时API》中“Device管理”章节的aclrtGetDeviceInfo接口查询设备的AIV物理核数。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [SIMT协作组简介（高级编程）](../../../../guides/programming_guide/advanced_programming/simt_cooperative_groups.md)（`explains`）：SIMT协作组简介（高级编程）说明协作组（cooperative_groups）是Ascend C SIMT编程模型的扩展，用于组织协作线程组。协作组使开发者能够控制线程协作的粒度，实现更丰富、更高效的并行处理逻辑。
- [GridGroupConstructor](grid_group_constructor.md)（`related`）：GridGroupConstructor 返回的对象是 grid 级 sync 的调用主体，形成获取对象到跨块同步的使用链。
- [IsValid](is_valid.md)（`same_topic`）：IsValid 专门回答该对象能否调用 sync；当前实现固定 true，随后可执行跨块同步。
- [sync（协作组）](../sync.md)（`same_topic`）：sync（协作组）说明同步指定协作组内的所有线程，功能等价于调用该协作组对象的成员函数sync()。
<!-- cannbot:related:end -->
