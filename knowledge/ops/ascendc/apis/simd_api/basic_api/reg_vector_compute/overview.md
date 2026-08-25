---
type: API
title: Reg矢量计算概述
description: Reg矢量计算API概述，直接操作Vector计算寄存器实现数据搬运与计算，较Memory矢量计算API提供更大开发自由度。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Reg矢量计算概述

Reg矢量计算API概述，直接操作Vector计算寄存器实现数据搬运与计算，较Memory矢量计算API提供更大开发自由度。

在SIMD编程场景下使用。用于启动SIMD VF（Vector Function）子任务。

本接口组包含 asc_vf_call, RegTensor, MaskReg, LoadAlign, StoreAlign。

本接口属于 Reg 矢量计算接口，操作 RegTensor 寄存器数据。

约束：asc_vf_call启动SIMD VF子任务时，子任务函数不能是类的成员函数，推荐使用普通函数或类静态函数，且入口函数必须使用__simd_vf__修饰宏。；asc_vf_call启动SIMD VF子任务时，入参仅支持Ascend C的内置数据类型（half、int32_t、uint32_t、float等）及其组成的指针、数组、结构体类型，且指针类型必须指向UB内存。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [AR 跨块循环放在 __simd_vf__ 只执行首块](../../../../runbooks/precision/simd_vf_chunk_loop_must_be_driven_by_aicore_wrapper.md)（`exemplifies`）：《AR 跨块循环放在 __simd_vf__ 只执行首块》给出“Ascend950 Reg kernel 把 AR 跨向量块状态机留在单次 __simd_vf__ 中时只完成首块；将循环上移至 __aicore__ wrapper，并在同址读改写调用之间加入 Vector barrier。”；该约束/探针可直接复现、解释或前置验证《Reg矢量计算概述》中的“Reg矢量计算API概述，直接操作Vector计算寄存器实现数据搬运与计算，较Memory矢量计算API提供更大开发自由度。”。
- [__simd_vf__ if constexpr 致 hoisted 报错](../../../../runbooks/compilation/simd_vf_if_constexpr_lowering_banned_exit_70.md)（`exemplifies`）：《__simd_vf__ if constexpr 致 hoisted 报错》说明dav-3510 上某 Reg __simd_vf__ 实现使用 if constexpr 与 constexpr trait 时，bisheng 后端报 Unsupported Inst must be hoisted 并退出 70；记录源码定位与编译边界，不提供未完成的 fallback 实现。；《Reg矢量计算概述》说明Reg矢量计算API概述，直接操作Vector计算寄存器实现数据搬运与计算，较Memory矢量计算API提供更大开发自由度。。二者在该编译失败锁定__simd_vf__中的if constexpr/trait lowering，同类模板隔离、helper/VF边界与后端崩溃用于交叉验证上存在可执行的直接衔接。
- [asc_vf_call](vf_call/asc_vf_call.md)（`related`）：《asc_vf_call》给出“在SIMD编程场景下使用。用于启动SIMD VF（Vector Function）子任务。”；该约束/探针可直接复现、解释或前置验证《Reg矢量计算概述》中的“Reg矢量计算API概述，直接操作Vector计算寄存器实现数据搬运与计算，较Memory矢量计算API提供更大开发自由度。”。
- [Reg矢量计算](reg_vector_compute.md)（`same_topic`）：Reg矢量计算 与《Reg矢量计算概述》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
<!-- cannbot:related:end -->
