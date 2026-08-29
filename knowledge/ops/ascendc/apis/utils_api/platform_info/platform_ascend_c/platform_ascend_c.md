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
