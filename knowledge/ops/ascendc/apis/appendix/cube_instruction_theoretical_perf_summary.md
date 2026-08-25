---
type: API
title: Cube指令理论性能汇总
description: 本节汇总介绍了主要的Cube指令的理论性能，以下内容针对如下型号生效：
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/cube_instruction_theoretical_perf_summary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Cube指令理论性能汇总

本节汇总介绍了主要的Cube指令的理论性能，以下内容针对如下型号生效： Ascend 950PR/Ascend 950DT Atlas A3 训练系列产品/Atlas A3 推理系列产品/Atlas A2 训练系列产品/Atlas A2 推理系列产品

涵盖以下类别：Mmad计算类指令理论性能汇总、矩阵计算搬入类指令理论性能汇总、矩阵计算搬出类指令理论性能汇总。

<!-- cannbot:related:start -->
## 相关

- [AscMmad](../simd_api/c_api/cube_compute/asc_mmad.md)（`related`）：AscMmad说明Ascend C矩阵乘加（Mmad）核心计算接口，封装昇腾NPU硬件矩阵乘加能力，用于全连接层、卷积层等神经网络算子开发。
- [Mmad](../simd_api/basic_api/cube_compute/mmad_compute/mmad.md)（`related`）：Mmad说明矩阵乘加核心计算接口，封装昇腾NPU硬件矩阵乘加能力，实现C=A*B+C，广泛用于全连接层、卷积层等算子开发。
- [Mmad接口边界值汇总](mmad_interface_boundary_value_summary.md)（`related`）：Mmad接口边界值汇总说明本节汇总介绍了Mmad计算接口在边界值输入下的输出结果，数据类型见基础API下的mmad，以下内容针对如下型号生效：。
<!-- cannbot:related:end -->
