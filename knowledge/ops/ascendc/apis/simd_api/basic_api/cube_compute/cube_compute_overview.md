---
type: API
title: 矩阵计算（ISASI）
description: AscendC 矩阵计算 ISASI 接口总览，涵盖搬入、Mmad 计算、搬出及辅助配置与关键特性说明。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 矩阵计算（ISASI）

Ascend C 矩阵计算 ISASI 接口导航页，提供基于底层指令的矩阵计算完整流程接口。
涵盖矩阵计算分形介绍、搬入（LoadData/DataCopy 等）、搬入辅助配置、Mmad 计算、Mmad 关键特性与辅助配置、搬出（DataCopy/Fixpipe）、搬出关键特性与寄存器配置。
相较于 TensorAPI，ISASI 接口更接近硬件指令层级，提供更细粒度的控制能力但编程复杂度更高。

<!-- cannbot:related:start -->
## 相关

- [普通矩阵计算流程（概述）](overview/cube_compute_flow.md)（`related`）：总览列出接口，而 CubeComputeFlow 明确把搬入、Mmad、搬出和辅助配置放入一条执行链，可用于从接口清单推导正确调用顺序。
- [矩阵计算](../../adv_api/cube_compute/cube_compute.md)（`related`）：高阶 Cube 入口面向 Matmul 等封装，而基础 ISASI 总览展开 GM/L1/L0A/L0B→Mmad→L0C 搬出链；在需要从高阶接口下沉定位通路或缓存约束时形成实质桥梁。
- [矩阵计算单元（概述）](overview/cube_compute_unit.md)（`related`）：CubeComputeUnit 说明 L0A/L0B/L0C 的角色和可直访缓存，为总览中的搬入与搬出通路为何受特定 Buffer 约束提供机制解释。
<!-- cannbot:related:end -->
