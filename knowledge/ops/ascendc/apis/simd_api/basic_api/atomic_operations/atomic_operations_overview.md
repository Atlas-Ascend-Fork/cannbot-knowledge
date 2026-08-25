---
type: API
title: 原子操作概述
description: 数据搬运随路原子操作接口用于对后续目的地址为GM的数据搬运开启原子操作，涉及的接口请参见表1。如下图1的左侧子图所示，未开启原子操作时，写入GM的数据搬运完成后，GM中原始数据将被新搬运数据完全覆盖。如图1右侧子图所示，当数据搬运随路原子操作接口被调用后，系统将为后续写入GM的数据搬运开启原子操作。此时，数据搬运完成后，GM中的最终数据由原始GM数据与新搬运数据共同决定。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/atomic_operations/atomic_operations_overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# 原子操作总览

原子操作提供对Global Memory的原子性读写能力，确保多核并发场景下数据一致性。包含两类：标量原子操作（AtomicAdd/Cas/Exch/Max/Min，直接对GM地址进行原子运算）和DMA随路原子操作（通过SetAtomicAdd等设置DMA搬运时的随路原子操作类型）。

标量原子操作仅Ascend 950PR/950DT支持；DMA随路原子操作支持更多产品型号。原子操作类型包括加、最大值、最小值、比较交换、交换等。

确定性计算注意事项：浮点数原子累加因不满足结合律，指令乱序可能导致非确定性结果。可通过DisableDmaAtomic禁用DMA原子操作或使用SetAtomicType配置原子类型来控制行为。

<!-- cannbot:related:start -->
## 相关

- [AtomicAdd](atomic_add.md)（`related`）：概述明确将标量地址原子加与 DMA 原子状态区分；AtomicAdd 是前者的具体即时读改写接口。
- [AtomicCas](atomic_cas.md)（`related`）：概述把 CAS 列为标量即时原子操作并说明其返回旧值语义，AtomicCas 页给出具体比较交换契约。
- [DisableDmaAtomic](disable_dma_atomic.md)（`related`）：概述要求 DMA 原子操作完成后关闭原子状态，DisableDmaAtomic 是避免状态泄漏到后续搬出的收尾动作。
- [SetAtomicAdd](set_atomic_add.md)（`related`）：概述中的 DMA 原子加需先 SetAtomicAdd 再搬出，并在结束后恢复状态；该页落实这一状态机。
- [原子操作](../../c_api/simd_atomic/atomic_operations.md)（`related`）：《原子操作概述》明确“数据搬运随路原子操作接口用于对后续目的地址为GM的数据搬运开启原子操作，涉及的接口请参见表1。如下图1的左侧子图所示，未开启原子操作时，写入GM的数据搬运完成后，GM中原始数据将被新搬运数据完全覆盖。如图1右侧子图所示，当数据搬运随路原子操作接口被调用后，系统将为后续写入GM的数据搬运开启原子操作。此时，数据搬运完成后，GM中的最终数据由原始GM数据与新搬运数据共同决定。”；它与《原子操作》的“SIMD C API原子操作类接口汇总，提供原子操作配置查询与设置，支持add、max、min等运算类型。”在实际调用参数、数据流或结果校验上直接衔接。
- [原子操作](../../../simt_api/atomic_operations/atomic_operations.md)（`related`）：原子操作 与《原子操作概述》的实质衔接是：SIMT 原子操作卡定义 GM/UB 作用域、读改写原子性以及不提供执行顺序；SIMT 指南、边界值表和 SIMD 原子概述用于选择作用域并验证边界，而不是替代同步。
- [关键特性说明（原子操作）](key_features.md)（`same_topic`）：关键特性页补充原子概述中的浮点 DMA 累加非确定性条件和规避动作。
- [原子操作边界值汇总（附录）](../../../appendix/atomic_operations_interface_boundary_value_summary.md)（`same_topic`）：焦点处理原子操作在边界输入下的结果解释；原子操作概述正文说明“数据搬运随路原子操作接口用于对后续目的地址为GM的数据搬运开启原子操作，涉及的接口请参见表1。如下图1的左侧子图所示，未开启原子操作时，写入GM的数据搬运完成后，GM中原始数据将被新搬运数据完全覆盖。如图1右侧子图所示，当数据搬运随路原子操作接口被调用后，系统将为后续写入GM的数”。候选给出边界表所依赖的原子读改写或随路原子语义，能据此解释极值、NaN 和溢出结果。
<!-- cannbot:related:end -->
