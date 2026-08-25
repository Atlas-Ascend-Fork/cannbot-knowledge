---
type: API
title: 同步控制
description: Reg矢量计算同步控制接口索引页，包含LocalMemBar。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/sync_control/sync_control.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 同步控制

提供 LocalMemBar 接口，用于 Reg 矢量计算宏函数内不同流水线之间的同步。通过模板参数指定 src 源流水线和 dst 目的流水线，目的流水线等待源流水线上所有指令完成后才执行。

支持的流水线类型包括 VEC_STORE、VEC_LOAD、SCALAR_STORE、SCALAR_LOAD 等。当读写指令使用相同寄存器时硬件自动保序，无需插入同步；使用不同寄存器时需手动插入。仅 Ascend 950PR/Ascend 950DT 支持，需在 VF 函数内调用。

<!-- cannbot:related:start -->
## 相关

- [arch35 __aicore__ 调 LocalMemBar 报 507035](../../../../../runbooks/compilation/arch35_aicore_localmembar_507035.md)（`exemplifies`）：《同步控制》说明Reg矢量计算同步控制接口索引页，包含LocalMemBar。；《arch35 __aicore__ 调 LocalMemBar 报 507035》说明Ascend950PR (arch35/dav_c310) 上 Reg::LocalMemBar<VEC_STORE,VEC_LOAD> 是 __simd_callee__ 函数，须在 __simd_vf__ (VF) 调用上下文内使用；从常规 __aicore__ kernel 函数直接调用触发运行时 507035 (AIV 错误)。本 trace 两次独立调用（旧 4-buffer 代码、新 5-buffer 重排代码）均 507035。作为 count-based Compare→Select mask 隐患的最小 sync 修复手段 banned。。二者在Reg同步页的核心是LocalMemBar；C API AscMemBar和架构故障卡给出同一内存可见性合同与非法调用边界上存在可执行的直接衔接。
- [同步控制](../../../c_api/reg/sync_control/sync_control.md)（`related`）：《同步控制》说明Reg矢量计算同步控制接口索引页，包含LocalMemBar。；《同步控制》说明寄存器侧同步控制类接口汇总，提供mem_bar内存屏障同步能力。。二者在Reg同步页的核心是LocalMemBar；C API AscMemBar和架构故障卡给出同一内存可见性合同与非法调用边界上存在可执行的直接衔接。
- [AscMemBar](../../../c_api/reg/sync_control/asc_mem_bar.md)（`same_topic`）：《同步控制》说明Reg矢量计算同步控制接口索引页，包含LocalMemBar。；《AscMemBar》说明Reg计算宏函数内不同流水线之间的同步指令，目的流水线等待源流水线所有指令完成后执行。。二者在Reg同步页的核心是LocalMemBar；C API AscMemBar和架构故障卡给出同一内存可见性合同与非法调用边界上存在可执行的直接衔接。
- [LocalMemBar](local_mem_bar.md)（`same_topic`）：《同步控制》说明Reg矢量计算同步控制接口索引页，包含LocalMemBar。；《LocalMemBar》说明Reg矢量计算宏函数内不同流水线之间的同步指令，目的流水线等待源流水线上所有指令完成才执行。。二者在Reg同步页的核心是LocalMemBar；C API AscMemBar和架构故障卡给出同一内存可见性合同与非法调用边界上存在可执行的直接衔接。
<!-- cannbot:related:end -->
