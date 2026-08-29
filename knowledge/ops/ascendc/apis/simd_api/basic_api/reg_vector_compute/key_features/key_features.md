---
type: API
title: 关键特性说明
description: Reg矢量计算关键特性说明，涵盖HardwareLoop硬件循环、指令双发优化、VF融合和数据搬运优化。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/key_features/key_features.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 关键特性说明

Reg矢量计算关键特性说明，涵盖HardwareLoop硬件循环、指令双发优化、VF融合和数据搬运优化。

本接口组包含 Reg矢量计算接口指令单双发汇总, 算子实践参考-指令双发优化, 算子实践参考-VF融合优化, 算子实践参考-连续非对齐场景优化。

本接口属于 Reg 矢量计算接口，操作 RegTensor 寄存器数据。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
