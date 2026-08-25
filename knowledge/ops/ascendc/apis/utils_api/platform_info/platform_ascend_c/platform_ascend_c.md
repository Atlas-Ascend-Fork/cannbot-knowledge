---
type: API
title: PlatformAscendC
description: PlatformAscendC平台信息查询接口索引。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/PlatformAscendC.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# PlatformAscendC

PlatformAscendC 是 Ascend C 提供的平台信息查询类，用于在 Host 侧获取硬件规格与运行时参数。主要接口包括核心数量查询（GetCoreNum、GetCoreNumAic、GetCoreNumAiv）、SoC 版本与 NPU 架构（GetSocVersion、GetCurNpuArch）、向量寄存器长度（GetVecRegLen）、内存容量与带宽（GetCoreMemSize、GetCoreMemBw）以及 Workspace 大小查询。

<!-- cannbot:related:start -->
## 相关

- [AddPlatformInfo](../../tiling_tuning/context_builder/add_platform_info.md)（`related`）：AddPlatformInfo 与《PlatformAscendC》的实质衔接是：AddPlatformInfo 把 PlatformInfo 注入 ContextBuilder，随后 BuildTiling/KernelRunContext 消费；PlatformAscendC/Manager 是平台能力信息的来源。
- [GetCoreMemSize](get_core_mem_size.md)（`related`）：GetCoreMemSize 与《PlatformAscendC》的实质衔接是：GetCoreMemSize 为 host tiling 提供各层容量；ReserveLocalMemory 会改变可用 UB，Matmul 空间查询与 UB 预算故障直接消费该值。
- [PlatformAscendCManager](../platform_ascend_c_manager.md)（`related`）：《PlatformAscendCManager》明确“Kernel直调场景下获取硬件平台信息的单例管理类，通过GetInstance获取PlatformAscendC指针以访问核数等平台信息。”；它与《PlatformAscendC》的“PlatformAscendC平台信息查询接口索引。”在实际调用参数、数据流或结果校验上直接衔接。
- [PlatformAscendC简介](platform_ascend_c_intro.md)（`same_topic`）：《PlatformAscendC简介》明确“在实现Host侧的Tiling函数时，可能需要获取一些硬件平台的信息，来支撑Tiling的计算，比如获取硬件平台的核数等信息。PlatformAscendC类提供获取这些平台信息的功能。”；它与《PlatformAscendC》的“PlatformAscendC平台信息查询接口索引。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
