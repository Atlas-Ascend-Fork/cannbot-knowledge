---
type: API
title: Reg矢量计算接口理论性能汇总
description: 本节汇总介绍了Reg矢量计算接口的理论性能，本节内容仅针对如下型号生效：
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/reg_vector_compute_interface_theoretical_perf_summary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Reg矢量计算接口理论性能汇总

本节汇总介绍了Reg矢量计算接口的理论性能，本节内容仅针对如下型号生效：

本接口属于 Reg 矢量计算接口。

本节汇总介绍了Reg矢量计算接口的理论性能，本节内容仅针对如下型号生效： Ascend 950PR/Ascend 950DT 本节汇总的理论性能均为单指令理论性能，实际性能还需考虑指令单双发情况，请参考Reg矢量计算接口指令单双发汇总。软仿实现的接口和数据类型不提供理论性能。

<!-- cannbot:related:start -->
## 相关

- [Reg矢量计算接口软仿情况汇总](reg_vector_compute_interface_soft_simulation_summary.md)（`related`）：底层硬件不支持该数据类型，通过多种接口组合软仿实现；软仿实现的接口和数据类型不提供理论性能。前者标明某些 dtype 是组合接口的软件仿真实现，后者明确这些软仿条目没有单指令理论性能；做接口性能选型时必须先排除软仿项再使用吞吐表。
<!-- cannbot:related:end -->
