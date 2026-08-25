---
type: API
title: 关键特性说明（原子操作）
description: 确定性计算是指在相同输入条件下，无论执行次数或执行环境如何变化，总能产生完全一致输出结果的计算过程。确定性计算为系统稳定性和实验可验证性提供保障。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/atomic_operations/key_features.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# 原子操作关键特性说明

确定性计算指在相同输入条件下总能产生完全一致输出结果的计算过程。原子操作场景下，浮点数原子累加因不满足结合律（(a+b)+c != a+(b+c)），当带随路原子操作的搬运指令达到3条及以上且发生乱序时，会产生非确定性结果。

非确定性计算产生的前提条件：原子操作类型为累加（最大值/最小值满足结合律不受影响）、数据类型为浮点数（整数加法满足结合律不受影响）、带随路原子操作的搬运指令达到3条及以上。

解决方案：通过DisableDmaAtomic禁用DMA原子操作；使用SetAtomicType配置原子类型；对浮点数累加结果进行reorder控制；或使用标量原子操作替代DMA随路原子操作。

<!-- cannbot:related:start -->
## 相关

- [DisableDmaAtomic](disable_dma_atomic.md)（`related`）：关键特性明确把 DisableDmaAtomic 作为浮点 DMA 原子累加结束和规避状态泄漏的动作。
- [SetAtomicType](set_atomic_type.md)（`related`）：SetAtomicType 用于按关键特性页选择 add/max/min 等原子类型，决定是否存在浮点加法非结合风险。
- [原子操作](atomic_operations.md)（`same_topic`）：原子操作 与《关键特性说明（原子操作）》的实质衔接是：原子操作总览与 CAS/Add/Exch/Min/Max 和 store atomic 配置共同界定并发更新选择。
- [原子操作概述](atomic_operations_overview.md)（`same_topic`）：关键特性页补充原子概述中的浮点 DMA 累加非确定性条件和规避动作。
<!-- cannbot:related:end -->
