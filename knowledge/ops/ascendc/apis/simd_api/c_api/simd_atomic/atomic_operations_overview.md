---
type: API
title: 原子操作概述（SIMD原子操作）
description: 数据搬运随路原子操作接口用于对后续目的地址为GM的数据搬运指令开启原子操作，涉及的接口请参见表1。如下图1的左侧子图所示，未开启原子操作时，写入GM的数据搬运完成后，GM中原始数据将被新搬运数据完全覆盖。如图1右侧子图所示，当数据搬运随路原子操作接口被调用后，系统将为后续写入GM的数据搬运开启原子操作。此时，数据搬运完成后，GM中的最终数据由原始GM数据与新搬运数据共同决定。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/simd_atomic/atomic_operations_overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 原子操作概述（SIMD原子操作）

数据搬运随路原子操作接口用于对后续目的地址为GM的数据搬运指令开启原子操作，涉及的接口请参见表1。如下图1的左侧子图所示，未开启原子操作时，写入GM的数据搬运完成后，GM中原始数据将被新搬运数据完全覆盖。如图1右侧子图所示，当数据搬运随路原子操作接口被调用后，系统将为后续写入GM的数据搬运开启原子操作。此时，数据搬运完成后，GM中的最终数据由原始GM数据与新搬运数据共同决定。
详见源文档获取完整说明。

<!-- cannbot:related:start -->
## 相关

- [AscSetAtomicMin](asc_set_atomic_min.md)（`related`）：AscSetAtomicMin 与《原子操作概述（SIMD原子操作）》的实质衔接是：AscSetAtomicMin 开启后续搬出取小，并需用 None 复位；SetAtomicMin/AtomicMin 和 store atomic 配置给出同一原子写回状态机。
- [原子操作](../../../simt_api/atomic_operations/atomic_operations.md)（`related`）：原子操作 与《原子操作概述（SIMD原子操作）》的实质衔接是：SIMT 原子操作卡定义 GM/UB 作用域、读改写原子性以及不提供执行顺序；SIMT 指南、边界值表和 SIMD 原子概述用于选择作用域并验证边界，而不是替代同步。
- [原子操作](atomic_operations.md)（`same_topic`）：《原子操作概述（SIMD原子操作）》明确“数据搬运随路原子操作接口用于对后续目的地址为GM的数据搬运指令开启原子操作，涉及的接口请参见表1。如下图1的左侧子图所示，未开启原子操作时，写入GM的数据搬运完成后，GM中原始数据将被新搬运数据完全覆盖。如图1右侧子图所示，当数据搬运随路原子操作接口被调用后，系统将为后续写入GM的数据搬运开启原子操作。此时，数据搬运完成后，GM中的最终数据由原始GM数据与新搬运数据共同决定。”；它与《原子操作》的“SIMD C API原子操作类接口汇总，提供原子操作配置查询与设置，支持add、max、min等运算类型。”在实际调用参数、数据流或结果校验上直接衔接。
- [原子操作边界值汇总（附录）](../../../appendix/atomic_operations_interface_boundary_value_summary.md)（`same_topic`）：焦点处理原子操作在边界输入下的结果解释；原子操作概述（SIMD原子操作）正文说明“数据搬运随路原子操作接口用于对后续目的地址为GM的数据搬运指令开启原子操作，涉及的接口请参见表1。如下图1的左侧子图所示，未开启原子操作时，写入GM的数据搬运完成后，GM中原始数据将被新搬运数据完全覆盖。如图1右侧子图所示，当数据搬运随路原子操作接口被调用后，系统将为后续写入GM”。候选给出边界表所依赖的原子读改写或随路原子语义，能据此解释极值、NaN 和溢出结果。
<!-- cannbot:related:end -->
