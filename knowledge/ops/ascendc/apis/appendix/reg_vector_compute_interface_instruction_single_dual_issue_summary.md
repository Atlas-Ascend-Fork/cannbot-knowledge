---
type: API
title: Reg矢量计算接口指令单双发汇总
description: 本节汇总介绍了Reg矢量计算接口指令单双发的情况，指令单发指1个Cycle能够执行一条指令，指令双发指1个Cycle能够执行两条指令。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/reg_vector_compute_interface_instruction_single_dual_issue_summary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Reg矢量计算接口指令单双发汇总

本节汇总介绍了Reg矢量计算接口指令单双发的情况，指令单发指1个Cycle能够执行一条指令，指令双发指1个Cycle能够执行两条指令。 针对寄存器：1个Cycle只能写两个Reg寄存器；针对UB：1个Cycle只能读两个VL（一个VL为256B），或者1个Cycle读一个VL和写一个VL。 本节内容不包含软仿类接口，仅针对如下型号生效： Ascend 950PR/Ascend 950DT 表 1 接口指令双发汇总

<!-- cannbot:related:start -->
## 相关

- [指令双发优化](../../guides/operator_practice/simd_operator_optimization/vector_compute/vf_optimization/dual_issue_optimization.md)（`explains`）：指令双发指1个Cycle能够执行两条指令；两条指令之间没有数据上的依赖关系。接口汇总给出单/双发能力上限，优化指南进一步给出无数据依赖与资源充足的启用条件以及拆分、展开 VF 的实现方法。
<!-- cannbot:related:end -->
