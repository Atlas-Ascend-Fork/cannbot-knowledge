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

- [arch35 __aicore__ 调 LocalMemBar 报 507035](../../../../../runbooks/compilation/arch35_aicore_localmembar_507035.md)（`exemplifies`）：Reg矢量计算宏函数内不同流水线之间的同步指令。；从 `__aicore__` 常规函数调 `Reg::LocalMemBar<VEC_STORE,VEC_LOAD>` 触发 507035 (AIV error)，两次独立代码版本（旧 4-buffer、新 5-buffer 重排）重编重跑均复现（来源平台:950；证据等级:tool_observed）。API 同步语义受 VF 调用上下文约束，runbook 给出错误上下文的可复现失败。
- [arch35 count Compare Select 异步VF 存读 RAW](../../../../../runbooks/precision/arch35_count_compare_select_vf_raw.md)（`exemplifies`）：读写场景下，当读指令使用的寄存器和写指令使用的寄存器相同时，可以触发寄存器保序，指令将会按照代码顺序执行，不需要插入同步指令，而当使用的寄存器不同时，如果要确保读写指令顺序执行，则需要插入同步指令，写写场景同理。；arch35 count-based Compare 为 `__simd_vf__`、经 `Reg::StoreAlign/StoreUnAlign` (VEC_STORE) 写 bMask 且内部无 LocalMemBar；count-based Select 经 `Reg::LoadAlign<DIST_US>` (VEC_LOAD) 读 bMask（来源平台：950；证据等级: tool_observed）。通用依赖规则解释该 Compare 到 Select 的具体 RAW 隐患。
- [NMS 950 Direct Invoke 算子知识](../../../../../operators/direct/cv/image/nms_950.md)（`related`）：“每次 Vector 更新必须在下一标量读取前完成”与“目的流水线将等待源流水线上所有指令完成才进行执行”把 NMS alive buffer 的生产消费顺序连接到 LocalMemBar 的流水线等待语义。
<!-- cannbot:related:end -->
