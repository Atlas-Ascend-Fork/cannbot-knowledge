---
type: API
title: TQueBind
description: TQueBind构造函数，用于创建TQueBind对象。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQueBind/TQueBind_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# TQueBind

头文件路径为："basic_api/kernel_tpipe.h"。

创建TQueBind对象。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [纯搬运类算子VECIN和VECOUT建议复用](../../../../../guides/operator_practice/simd_operator_optimization/memory_access/vecin_vecout_reuse.md)（`explains`）：纯搬运类算子VECIN和VECOUT建议复用 与《TQueBind》的实质衔接是：VECIN/VECOUT 复用依赖 TQueBind 将输入输出逻辑位置绑定到同一物理队列；高效搬运、UB 融合和优化总览说明这种复用减少搬运与 UB 占用的适用边界。
- [FreeAllEvent](free_all_event.md)（`same_topic`）：《FreeAllEvent》处理“释放TQueBind队列中申请的所有同步事件，便于在Buffer数量超过同步事件限制时重新申请队列。”。《TQueBind》明确“TQueBind构造函数，用于创建TQueBind对象。”，可直接用于核对FreeAllEvent 对 TQueBind 事件和 Alloc/Fetch/Release event ID 生命周期的回收合同。
- [TQueBind简介](t_que_bind_intro.md)（`same_topic`）：构造函数卡只说明创建对象，简介补充 TQueBind 如何按源/目的 TPosition 选择内存并插入同步事件，以及何时应使用 TQueBind 而非简化 TQue。
<!-- cannbot:related:end -->
