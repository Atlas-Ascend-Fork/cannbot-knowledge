---
type: API
title: UnitFlag
description: unitFlag的核心功能体现为：Mmad和FixPipe接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C
  Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute_key_features/UnitFlag.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# UnitFlag

Mmad 和 Fixpipe 接口的单元标志机制，以 L0C Buffer 512B 内存块为粒度实现精细化数据同步，降低同步延迟。unitFlag=2 时开启但不改变标志位（Mmad 写等待 flag=0 后写入保持 0；Fixpipe 读等待 flag=1 后读取保持 1）；unitFlag=3 时开启并改变标志位（Mmad 写后设 1；Fixpipe 读后设 0）。

K 轴迭代场景：前 n-1 次 Mmad 设 unitFlag=2 保持写入能力，最后 1 次设 3 通知 Fixpipe 可读；Fixpipe 设 3 读后恢复为 0。需配合 SetMMColumnMajor/SetMMRowMajor 设置方向：Fixpipe 开启 NZ2ND/ChannelMerge 时用 SetMMRowMajor，否则用 SetMMColumnMajor。Mmad 和 Fixpipe 须同步开启 unitFlag，建议计算量与搬出量一致，否则可通过 SetFixPipeConfig() 重置 L0C Buffer 状态。

<!-- cannbot:related:start -->
## 相关

- [Matmul高阶API开启UnitFlag](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_unit_flag.md)（`explains`）：Mmad 和 Fixpipe 接口的单元标志机制，以 L0C Buffer 512B 内存块为粒度实现精细化数据同步；UnitFlag功能为AIC核中MMAD计算指令和FIXPIPE数据搬运指令提供了基于内存访问的细粒度同步；机制页给出 flag 状态转换，调优案例给出开启条件、模板约束和 Profiling 验证。
- [AscSetMmadDirectionM](../../../c_api/cube_compute/asc_set_mmad_direction_m.md)（`related`）：方向 M 卡把使用条件限定为“在开启UnitFlag的场景下，当L0C Buffer上结果分形的生成顺序与数据搬出指令的搬出顺序保持一致时，可以获得更好的性能表现”；UnitFlag 卡说明“Mmad 和 Fixpipe 接口的单元标志机制，以 L0C Buffer 512B 内存块为粒度实现精细化数据同步，降低同步延迟。”，解释方向配置为何必须与细粒度生产/消费顺序一致。
- [SetMMColumnMajor/SetMMRowMajor](../mmad_compute_aux_config/set_mm_column_major_set_mm_row_major.md)（`related`）：开启 unitFlag 时需配合设置：Fixpipe 开启 NZ2ND/ChannelMerge 时用 SetMMRowMajor，否则用 SetMMColumnMajor。；需配合 SetMMColumnMajor/SetMMRowMajor 设置方向：Fixpipe 开启 NZ2ND/ChannelMerge 时用 SetMMRowMajor，否则用 SetMMColumnMajor。；两卡从方向配置与 UnitFlag 两端给出同一组合契约，直接支撑实现选型。
<!-- cannbot:related:end -->
