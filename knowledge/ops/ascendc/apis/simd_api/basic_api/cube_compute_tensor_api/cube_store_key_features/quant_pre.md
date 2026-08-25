---
type: API
title: 基础API随路量化
description: 随路量化是矩阵计算结果从L0C Buffer搬出到Global Memory或Unified Buffer过程中的数据转换能力。L0C Buffer到Global
  Memory/Unified Buffer搬运根据是否传入quant参数自动选择不量化、直接cast、scalar量化或tensor量化模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_store_key_features/quant_pre.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 基础API随路量化

随路量化是矩阵计算结果从L0C Buffer搬出到Global Memory或Unified Buffer过程中的数据转换能力。L0C Buffer到Global

本接口属于 Cube 矩阵计算接口。

约束：tensor量化参数张量应位于L1 Buffer，元素类型为uint64_t，地址要求32字节对齐。；量化参数不能为inf、nan或非规格化数。该约束属于硬件约束，接口不单独检查参数值。；RoundMode::HYBRID仅在源类型为float、目的类型为hifloat8_t的量化输出场景支持。；不传入quant时，仅支持不量化输出或float到half/bfloat16_t的直接cast输出。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
