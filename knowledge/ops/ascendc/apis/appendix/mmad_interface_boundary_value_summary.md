---
type: API
title: Mmad接口边界值汇总
description: 本节汇总介绍了Mmad计算接口在边界值输入下的输出结果，数据类型见基础API下的mmad，以下内容针对如下型号生效：
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/mmad_interface_boundary_value_summary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Mmad接口边界值汇总

本节汇总介绍了Mmad计算接口在边界值输入下的输出结果，数据类型见基础API下的mmad，以下内容针对如下型号生效： - Ascend 950PR/Ascend 950DT - Atlas A3 训练系列产品/Atlas A3 推理系列产品 - Atlas A2 训练系列产品/Atlas A2 推理系列产品 表1 Mmad特殊值 边界值输入的计算结果说明

适用：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。

<!-- cannbot:related:start -->
## 相关

- [Cube矩阵计算编程](../../guides/programming_guide/programming_model/ai_core_simd_programming/c_pointer_programming/cube_matrix_computation.md)（`explains`）：Cube矩阵计算编程 与《Mmad接口边界值汇总》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [AscMmad](../simd_api/c_api/cube_compute/asc_mmad.md)（`related`）：AscMmad 与《Mmad接口边界值汇总》的实质衔接是：AscMmad 在 AIC 上消费 L0A/L0B 并累加到 L0C；Mmad 约束、方向/HF32 配置、Cube 流程和 AIV 误调用故障共同覆盖实际调用边界。
- [AscSetFp32Mode](../simd_api/c_api/cube_compute/asc_set_fp32_mode.md)（`related`）：AscSetFp32Mode 与《Mmad接口边界值汇总》的实质衔接是：AscSetFp32Mode 与 HF32 round/enable/trans 配置共同决定 AscMmad 的 FP32/HF32 计算模式，Mmad 约束和 HF32 指南说明精度与方向设置。
- [Cube指令理论性能汇总](cube_instruction_theoretical_perf_summary.md)（`related`）：Mmad接口边界值汇总说明本节汇总介绍了Mmad计算接口在边界值输入下的输出结果，数据类型见基础API下的mmad，以下内容针对如下型号生效：。
- [Mmad](../simd_api/basic_api/cube_compute/mmad_compute/mmad.md)（`same_topic`）：Mmad 边界值附录明确以基础 API Mmad 的数据类型与计算语义为前提；接口卡提供调用参数，附录提供特殊值输出 oracle。
<!-- cannbot:related:end -->
