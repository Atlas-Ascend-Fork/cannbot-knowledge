---
type: API
title: SIMT接口软仿情况汇总
description: 本节按照SIMT API文档所在目录分级汇总各接口的软仿情况。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/SIMT_interface_soft_simulation_summary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# SIMT接口软仿情况汇总

本节按照SIMT API文档所在目录分级汇总各接口的软仿情况。 非软仿接口是指使用单一硬件指令完成操作的接口；软仿接口是指由编译器实现，或由上层接口通过拼接多条硬件指令实现功能的接口。

涵盖以下类别：Warp函数、LaneID类函数、Warp Reduce类函数、Warp Shfl类函数、Warp Vote类函数、协作组、coalesced_group、thread_block、thread_block_tile、原子操作。

<!-- cannbot:related:start -->
## 相关

- [SIMT接口精度标准汇总](simt_interface_precision_standard_summary.md)（`related`）：软仿汇总标明哪些 SIMT 接口不是硬件原生实现，这是解释精度标准和平台差异的必要条件。
- [Reg矢量计算接口软仿情况汇总](reg_vector_compute_interface_soft_simulation_summary.md)（`same_topic`）：Reg矢量计算接口软仿情况汇总 与《SIMT接口软仿情况汇总》的衔接是：两张汇总采用同一‘单指令或编译器/上层拼接软仿’判定口径，SIMT汇总可用于区分 Reg 搬入搬出双操作数软仿与另一执行模型的软仿边界。
<!-- cannbot:related:end -->
