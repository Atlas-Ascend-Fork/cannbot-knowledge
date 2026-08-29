---
type: Guide
title: Ascend 950PR/Ascend 950DT新增特性导航
description: 本文档索引Ascend 950PR/Ascend 950DT（NPU架构版本3510）相比上一代（2201）新增的硬件特性，以及每个特性对应的编程模型、API接口和算子实践资料链接。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/asc_950_feature_guide.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Ascend 950PR/Ascend 950DT新增特性导航

本文档索引 Ascend 950PR/Ascend 950DT（NPU 架构版本 3510）相比上一代（2201）新增的硬件特性，以及每个特性对应的编程模型、API 接口和算子实践资料链接。
新增特性包括 RegBase 架构（Vector 计算从 MemBase 切换到 RegBase）、SIMT 编程模型（线程级并行）、SIMD 与 SIMT 混合编程、HiF8 数据类型、UB 到 L1 Buffer 通路、L0C 到 UB 通路、ND-DMA 搬运指令、SSBuffer 核间存储、Mutex 同步、CrossCore 核间同步、MX 数据类型、Fixpipe 增强、UB bank 结构变化等。
适用于 __NPU_ARCH__ 为 3510 的芯片，架构变更详情参考 2201 到 3510 架构变更文档。
