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

<!-- cannbot:related:start -->
## 相关

- [Copy](../cube_compute_store/copy_l0_c_to_gm.md)（`related`）：随路量化是矩阵计算结果从L0C Buffer搬出到Global Memory或Unified Buffer过程中的数据转换能力。；支持场景：连续数据搬出、随路格式转换（Fractal到ND/NZ等）、Batch多矩阵搬出、随路量化（QuantPre）、随路ReLU（ReluPre）、F32通道切分（F32ChannelSplit）、INT8通道合并（Int8ChannelMerge）。；候选是 QuantPre 在 L0C 到 GM 输出路径上的直接消费接口。
- [Copy](../cube_compute_store/copy_l0_c_to_ub.md)（`related`）：随路量化是矩阵计算结果从L0C Buffer搬出到Global Memory或Unified Buffer过程中的数据转换能力。；通过统一Copy接口将L0C Buffer数据搬运到Unified Buffer，用于矩阵计算结果在Vector侧进一步处理。；候选给出 QuantPre 的另一条 L0C 到 UB 输出消费路径。
- [CopyL1ToFixpipe](../cube_compute_load/copy_l1_to_fixpipe.md)（`related`）：tensor量化参数张量应位于L1 Buffer，元素类型为uint64_t，地址要求32字节对齐。；通过统一Copy接口将L1 Buffer数据搬运到Fixpipe，用于矩阵计算中Fixpipe数据处理。；候选是 L1 量化参数进入 Fixpipe 的生产消费步骤。
<!-- cannbot:related:end -->
