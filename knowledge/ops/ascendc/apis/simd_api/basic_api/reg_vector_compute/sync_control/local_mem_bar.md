---
type: API
title: LocalMemBar
description: Reg矢量计算宏函数内不同流水线之间的同步指令，目的流水线等待源流水线上所有指令完成才执行。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/sync_control/LocalMemBar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# LocalMemBar

头文件路径为："basic_api/reg_compute/kernel_reg_compute_membar_intf.h"。

Reg矢量计算宏函数内不同流水线之间的同步指令。该同步指令指定src源流水线和dst目的流水线，如下图所示，目的流水线将等待源流水线上所有指令完成才进行执行。读写场景下，当读指令使用的寄存器和写指令使用的寄存器相同时，可以触发寄存器保序，指令将会按照代码顺序执行，不需要插入同步指令，而当使用的寄存器不同时，如果要确保读写指令顺序执行，则需要插入同步指令，写写场景同理。MemType用于标识不同的流水线类型，其具体取值与含义

参数：src: 源流水线，类型为MemType，具体参见表2 MemType取值说明。；dst: 目的流水线，类型为MemType，具体参见表2 MemType取值说明。；VEC_STORE: SIMD_VF函数内矢量写UB流水线。 对应寄存器到UB的搬运指令，如StoreAlign、StoreUnAlign、Store。；VEC_LOAD: SIMD_VF函数内矢量读UB流水线。 对应UB到寄存器的搬运指令，如LoadAlign、LoadUnAlign、Load。；SCALAR_STORE: SIMD_VF函数内标量写UB流水线。 对应标量写入UB的指令。；SCALAR_LOAD: SIMD_VF函数内标量读UB流水线。 对应UB读取标量的指令。；VEC_ALL: SIMD_VF函数内所有矢量读写UB流水线。；SCALAR_ALL: SIMD_VF函数内所有标量读写UB流水线。

支持数据类型：无。

约束：读写依赖的场景下，如果读指令和写指令使用的寄存器相同，会触发寄存器保序，指令将会按照代码顺序执行，无需额外插入同步指令。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [arch35 __aicore__ 调 LocalMemBar 报 507035](../../../../../runbooks/compilation/arch35_aicore_localmembar_507035.md)（`exemplifies`）：《arch35 __aicore__ 调 LocalMemBar 报 507035》处理“Ascend950PR (arch35/dav_c310) 上 Reg::LocalMemBar<VEC_STORE,VEC_LOAD> 是 __simd_callee__ 函数，须在 __simd_vf__ (VF) 调用上下文内使用；从常规 __aicore__ kernel 函数直接调用触发运行时 507035 (AIV 错误)。本 trace 两次独立调用（旧 4-buffer 代码、新 5-buffer 重排代码）均 507035。作为 count-based Compare→Select mask 隐患的最小 sync 修复手段 banned。”。《LocalMemBar》明确提供“Reg矢量计算宏函数内不同流水线之间的同步指令，目的流水线等待源流水线上所有指令完成才执行。”，其参数、调用或验证步骤直接接入LocalMemBar 507035 的 Compare/Select 调用触发、屏障约束和可执行替代。
- [arch35 count Compare Select 异步VF 存读 RAW](../../../../../runbooks/precision/arch35_count_compare_select_vf_raw.md)（`exemplifies`）：arch35 count Compare Select 异步VF 存读 RAW 与《LocalMemBar》的实质衔接是：该故障是 count Compare 将 packed mask 异步写 UB、随后 Select 重新 Load 的 VEC_STORE→VEC_LOAD RAW；GetValue 探针、LocalMemBar/pipe 同步边界和准确 Compare/Select 接口共同支持确诊与修复。
- [CheckLocalMemoryIA](../../debug_interface/exception_detection/check_local_memory_ia_isasi.md)（`related`）：LocalMemBar 与《CheckLocalMemoryIA》的实质衔接是：LocalMemBar 只解决本地内存可见性，AscMemBar/核内同步材料给出作用域；RAW 故障与 arch35 编译卡分别验证缺 barrier 和错误执行域的后果。
- [SetFlag/WaitFlag](../../sync_control/intra_core_sync/set_flag_wait_flag.md)（`related`）：LocalMemBar 与《SetFlag/WaitFlag》的实质衔接是：LocalMemBar 只解决本地内存可见性，AscMemBar/核内同步材料给出作用域；RAW 故障与 arch35 编译卡分别验证缺 barrier 和错误执行域的后果。
- [同步控制](../../../c_api/reg/sync_control/sync_control.md)（`related`）：LocalMemBar 与《同步控制》的实质衔接是：LocalMemBar 只解决本地内存可见性，AscMemBar/核内同步材料给出作用域；RAW 故障与 arch35 编译卡分别验证缺 barrier 和错误执行域的后果。
- [核内同步](../../sync_control/intra_core_sync/intra_core_sync.md)（`related`）：LocalMemBar 与《核内同步》的实质衔接是：LocalMemBar 只解决本地内存可见性，AscMemBar/核内同步材料给出作用域；RAW 故障与 arch35 编译卡分别验证缺 barrier 和错误执行域的后果。
- [核内同步能力概述](../../sync_control/intra_core_sync/intra_core_sync_overview.md)（`related`）：LocalMemBar 与《核内同步能力概述》的实质衔接是：LocalMemBar 只解决本地内存可见性，AscMemBar/核内同步材料给出作用域；RAW 故障与 arch35 编译卡分别验证缺 barrier 和错误执行域的后果。
- [AscMemBar](../../../c_api/reg/sync_control/asc_mem_bar.md)（`same_topic`）：LocalMemBar 是 C++ Reg 路线的同类流水同步接口，可与 AscMemBar 对照源/目的流水依赖。
- [同步控制](sync_control.md)（`same_topic`）：《同步控制》说明Reg矢量计算同步控制接口索引页，包含LocalMemBar。；《LocalMemBar》说明Reg矢量计算宏函数内不同流水线之间的同步指令，目的流水线等待源流水线上所有指令完成才执行。。二者在Reg同步页的核心是LocalMemBar；C API AscMemBar和架构故障卡给出同一内存可见性合同与非法调用边界上存在可执行的直接衔接。
<!-- cannbot:related:end -->
