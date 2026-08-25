---
type: API
title: Vector逻辑架构
description: Vector计算单元专用于执行向量计算。如下图所示，高亮部分展示了Vector计算单元及其关联的存储单元。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/Vector_logical_arch/Vector_logical_arch.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Vector逻辑架构

Vector计算单元专用于执行向量计算。如下图所示，高亮部分展示了Vector计算单元及其关联的存储单元。

本接口组包含 避免bank冲突（NPU架构版本2201）, 避免bank冲突（NPU架构版本3510）。

本接口属于 UB 矢量计算接口。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [避免bank冲突（NPU架构版本2201）](../../../../../guides/operator_practice/simd_operator_optimization/memory_access/avoid_ub_bank_conflict/avoid_bank_conflict_npu_arch_2201.md)（`explains`）：Vector 逻辑架构中的 UB bank、矢量访问宽度和冲突机制是该指南调整地址错位以避开 bank 冲突的硬件依据。
<!-- cannbot:related:end -->
