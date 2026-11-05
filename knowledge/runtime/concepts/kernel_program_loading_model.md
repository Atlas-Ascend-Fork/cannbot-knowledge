---
type: Concept
title: Kernel 二进制加载与执行模型
description: CANN Runtime 内核二进制经 BinaryLoader→Program（ElfProgram 解析 ELF / PlainProgram 注册 CPU 内核）→Kernel→KernelTable 管理；支持按核函数名称（GetKernelByName）与按标识/tilingKey（AllKernelLookup 二分查找）两种查找；设备加载经 Program::Load2Device（4K 对齐 + H2D）在 GetFunction 时触发；Kernel 由所属 Program 基地址计算设备侧函数地址。
tags:
- task.design
- topic.architecture
- topic.implementation.kernel_launch
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/design/modules/kernel/kernel.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/kernel/program.hpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/kernel/kernel.hpp
  role: implementation
created_at: '2026-09-30T00:00:00Z'
updated_at: '2026-11-02T08:02:29Z'
platforms: []
---

# Kernel 二进制加载与执行模型

本卡蒸馏 Runtime 核心层内核二进制的注册、查找、设备加载与执行地址获取流程，供理解 `aclrtBinaryLoad*`/`aclrtBinaryGetFunction*`/`aclrtLaunchKernel` 的内部模型时参考。结论基于固定 commit `b523035a` 的源码核验，不构成跨版本承诺；平台范围保持未知。

## 对象组成

- **BinaryLoader**：注册入口，从文件或内存加载二进制并创建 Program。
- [`Program`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/kernel/program.hpp#L94)（`NoCopy`）：管理内核二进制与查找，维护**名称映射**与 **tilingKey 有序表**两套查找机制。两个子类：
  - [`ElfProgram`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/kernel/program.hpp#L341)：解析 ELF 并经 [`UnifiedKernelRegister()`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/kernel/program.hpp#L361) 注册 AI Core/MIX 内核。
  - [`PlainProgram`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/kernel/program.hpp#L319)：注册 CPU（AICPU）内核的简单二进制。
- [`Kernel`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/kernel/kernel.hpp#L41)：维护内核元信息（名称、偏移、tilingKey、所属 `program_`）。
- [`KernelTable`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/kernel/kernel.hpp#L339)：全局 stub→Kernel 有序映射表，二分查找，支持按 Program 批量卸载。

## 注册 → 查找 → 加载 → 执行

1. **注册**：`aclrtBinaryLoadFromFile`/`FromData` → `BinaryLoader::Load` → [`Program::Register`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/kernel/program.hpp#L203)；ELF 走 `ElfProgram::UnifiedKernelRegister`，CPU 走 PlainProgram 注册。
2. **查找**（两种方式）：
   - 按名称：`aclrtBinaryGetFunction` → [`Program::GetKernelByName`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/kernel/program.hpp#L217)。
   - 按核函数标识/tilingKey：`aclrtBinaryGetFunctionByEntry` → [`Program::AllKernelLookup`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/kernel/program.hpp#L214)（二分查找）。
3. **设备加载**：[`Program::Load2Device`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/kernel/program.hpp#L247) 分配设备内存（4K 对齐）+ H2D 拷贝，在 `aclrtBinaryGetFunction` 内部触发（设计文档）。
4. **执行**：`aclrtLaunchKernel` 下发时，[`Kernel::GetFunctionDevAddr`](../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/core/inc/kernel/kernel.hpp#L153) 由所属 Program 的设备基地址直接计算设备侧函数地址，配合参数加载组装为计算类 Task 下发（见 [Task 模型](task_management_model.md)）。

## 两套查找机制的意义

Program 同时维护名称映射（`kernelNameMap_`）与 tilingKey 有序表（支持 `AllKernelLookup` 二分查找），对应"按名"与"按标识"两种入口；KernelTable 以 stub→Kernel 有序表做全局二分查找并支持按 Program 批量卸载，是内核表快速查找的性能来源。

## 适用条件与失效边界

- 适用：理解二进制注册/查找/设备加载/执行地址获取的对象流转，以及 ELF 与 CPU 内核两条注册路径；适用于固定 commit `b523035a` 核心层实现。
- 失效边界：ELF 解析、`Load2Device` 的对齐与加载细节随平台/代际不同；AI Core/MIX/AICPU 的支持与注册分支依赖具体芯片；设备加载触发时机以实现为准。
- 验证方式：以 `kernel/program.hpp`（Program/ElfProgram/PlainProgram）与 `kernel/kernel.hpp`（Kernel/KernelTable）为准；设计文档 `docs/zh/design/modules/kernel/kernel.md` 作导读，冲突时以源码为准。

## 相关知识

- [Task 任务类型、资源管理与下发回收模型](task_management_model.md)——内核执行作为计算类 Task 下发
- [Stream SQ/CQ 异步执行与任务回收机制](stream_sqcq_async_mechanism.md)——Kernel 任务经 Stream 下发
- [Kernel 加载与执行 API](../apis/kernel_loading_and_execution/index.md)——二进制加载、核函数查询、参数组装与启动接口
