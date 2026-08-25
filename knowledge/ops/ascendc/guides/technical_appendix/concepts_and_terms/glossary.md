---
type: Guide
title: 技术附录术语表
description: AscendC::TPosition::A1代表设备上用于矩阵计算的逻辑内存，用于存放左矩阵，物理存储对应AI Core的L1 Buffer。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/technical_appendix/concepts_and_terms/glossary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 术语表

Ascend C开发中常用术语和缩略语定义。涵盖存储相关术语（GM、UB、L1/L0A/L0B/L0C Buffer、L2 Cache、BiasTable Buffer、Fixpipe Buffer及对应TPosition逻辑位置A1/A2/B1/B2/CO1/CO2等）、计算单元术语（AI Core、Cube Core、Vector Core、Scalar、Cube、Vector）、编程模型术语（Kernel、Tiling、TilingData、TilingFunc、TilingKey、Pipe、SPMD、SIMD、SIMT、Block、BlockID、DataBlock、Repeat、Mask、DoubleBuffer）、架构术语（Host、Device、DMA、MTE1/MTE2/MTE3、Fixpipe、DCache、ICache）以及SuperKernel二进制融合技术等。TPosition用抽象逻辑位置表达多级存储，隐藏硬件细节。
