---
type: API
title: Mmad计算关键特性说明
description: 本节介绍Mmad矩阵乘计算中的GEMV、HF32和UnitFlag等关键特性，帮助理解不同计算模式、精度模式和细粒度同步机制。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/mmad_compute_key_features/mmad_compute_key_features.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Mmad计算关键特性说明

本节介绍Mmad矩阵乘计算中的GEMV、HF32和UnitFlag等关键特性，帮助理解不同计算模式、精度模式和细粒度同步机制。

阅读本节前，建议先了解Mmad接口和矩阵计算分形介绍。

- **GEMV**

- **HF32**

- **UnitFlag**

<!-- cannbot:related:start -->
## 相关

- [Matmul高阶API开启UnitFlag](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_unit_flag.md)（`explains`）：关键特性页只概述 UnitFlag；案例给出 enUnitFlag 开关、支持模板、与 L0C 累加/搬出组合的限制及适用瓶颈，能直接指导落地。
- [SetHF32Mode](../../cube_compute/mmad_compute_aux_config/set_hf32_mode.md)（`related`）：关键特性页描述 HF32 的性能/精度权衡，SetHF32Mode 是真正启停该舍入行为的配置接口，并指向独立舍入方式设置。
- [UnitFlag](unit_flag.md)（`same_topic`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《Mmad计算关键特性说明》提供“本节介绍Mmad矩阵乘计算中的GEMV、HF32和UnitFlag等关键特性，帮助理解不同计算模式、精度模式和细粒度同步机制。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
- [基础APIGEMV](gemv.md)（`same_topic`）：《基础APIGEMV》处理“GEMV的核心功能体现为：当矩阵A的维度M取值为1时，接口可以手动启用GEMV功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。”。《Mmad计算关键特性说明》明确提供“本节介绍Mmad矩阵乘计算中的GEMV、HF32和UnitFlag等关键特性，帮助理解不同计算模式、精度模式和细粒度同步机制。”，其参数、调用或验证步骤直接接入GEMV 的 Mmad 形状、行主序布局、对齐、Tiling 和结果验证。
<!-- cannbot:related:end -->
