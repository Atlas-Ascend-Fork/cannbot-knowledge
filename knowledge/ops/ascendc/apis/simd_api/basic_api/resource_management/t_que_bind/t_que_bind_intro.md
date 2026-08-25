---
type: API
title: TQueBind简介
description: TQueBind绑定源逻辑位置和目的逻辑位置，根据源位置和目的位置，来确定内存分配的位置 、插入对应的同步事件，帮助开发者解决内存分配和管理、同步等问题。Tque是TQueBind的简化模式。通常情况下开发者使用TQue进行编程，TQueBind对外提供一些特殊数据通路的内存管理和同步控制，涉及这些通路时可以直接使用TQueBind。
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQueBind/TQueBind_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# TQueBind简介

TQueBind绑定源逻辑位置和目的逻辑位置，根据源位置和目的位置，来确定内存分配的位置 、插入对应的同步事件，帮助开发者解决内存分配和管理、同步等问题。Tque是TQueBind的简化模式。通常情况下开发者使用TQue进行编程，TQueBind对外提供一些特殊数据通路的内存管理和同步控制，涉及这些通路时可以直接使用TQueBind。

<!-- cannbot:related:start -->
## 相关

- [PadMode/单参 EnQue 在 CANN9.0.0 编译失败](../../../../../runbooks/compilation/padmode_enque_cann9_0_0.md)（`exemplifies`）：TQueBind简介 与《PadMode/单参 EnQue 在 CANN9.0.0 编译失败》的实质衔接是：TQueBind 与 TQue 的差别在绑定两队列；复用、EnQue 重载和 InitBuffer 故障卡直接约束该资源生命周期。
- [TQue InitBuffer 须传深度和 uint32 长度](../../../../../runbooks/compilation/tque_initbuffer_requires_depth_and_uint32_length.md)（`exemplifies`）：TQueBind简介 与《TQue InitBuffer 须传深度和 uint32 长度》的实质衔接是：TQueBind 与 TQue 的差别在绑定两队列；复用、EnQue 重载和 InitBuffer 故障卡直接约束该资源生命周期。
- [纯搬运类算子VECIN和VECOUT建议复用](../../../../../guides/operator_practice/simd_operator_optimization/memory_access/vecin_vecout_reuse.md)（`explains`）：TQueBind简介 与《纯搬运类算子VECIN和VECOUT建议复用》的实质衔接是：TQueBind 与 TQue 的差别在绑定两队列；复用、EnQue 重载和 InitBuffer 故障卡直接约束该资源生命周期。
- [FreeAllEvent](free_all_event.md)（`same_topic`）：《FreeAllEvent》处理“释放TQueBind队列中申请的所有同步事件，便于在Buffer数量超过同步事件限制时重新申请队列。”。《TQueBind简介》明确“TQueBind绑定源逻辑位置和目的逻辑位置，根据源位置和目的位置，来确定内存分配的位置 、插入对应的同步事件，帮助开发者解决内存分配和管理、同步等问题。Tque是TQueBind的简化模式。通常情况下开发者使用TQue进行编程，TQueBind对外提供一些特殊数据通路的内存管理和同步控制，涉及这些通路时可以直接使用TQueBind。”，可直接用于核对FreeAllEvent 对 TQueBind 事件和 Alloc/Fetch/Release event ID 生命周期的回收合同。
- [TQueBind](t_que_bind_constructor.md)（`same_topic`）：构造函数卡只说明创建对象，简介补充 TQueBind 如何按源/目的 TPosition 选择内存并插入同步事件，以及何时应使用 TQueBind 而非简化 TQue。
- [TQue简介](../t_que/t_que_intro.md)（`same_topic`）：TQueBind简介 与《TQue简介》的实质衔接是：TQueBind 与 TQue 的差别在绑定两队列；复用、EnQue 重载和 InitBuffer 故障卡直接约束该资源生命周期。
<!-- cannbot:related:end -->
