---
type: API
title: 同步控制
description: 寄存器侧同步控制类接口汇总，提供mem_bar内存屏障同步能力。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/sync_control/sync_control.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 同步控制

提供 asc_mem_bar 接口，用于 Reg 计算宏函数内不同流水线之间的同步。通过 mem_type 参数指定源流水线和目的流水线，目的流水线等待源流水线上所有指令完成后才执行。

支持的流水线类型组合包括 VV_ALL、VST_VLD、VLD_VST、VST_VST、VS_ALL、VST_LD、VLD_ST 等，覆盖 VEC_STORE/VEC_LOAD/SCALAR_STORE/SCALAR_LOAD 之间的同步。当读写指令使用相同寄存器时硬件自动保序，使用不同寄存器时需手动插入同步。仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [LocalMemBar](../../../basic_api/reg_vector_compute/sync_control/local_mem_bar.md)（`related`）：LocalMemBar 与《同步控制》的实质衔接是：LocalMemBar 只解决本地内存可见性，AscMemBar/核内同步材料给出作用域；RAW 故障与 arch35 编译卡分别验证缺 barrier 和错误执行域的后果。
- [同步控制](../../../basic_api/reg_vector_compute/sync_control/sync_control.md)（`related`）：《同步控制》说明Reg矢量计算同步控制接口索引页，包含LocalMemBar。；《同步控制》说明寄存器侧同步控制类接口汇总，提供mem_bar内存屏障同步能力。。二者在Reg同步页的核心是LocalMemBar；C API AscMemBar和架构故障卡给出同一内存可见性合同与非法调用边界上存在可执行的直接衔接。
<!-- cannbot:related:end -->
