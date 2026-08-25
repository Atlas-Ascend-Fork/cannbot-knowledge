---
type: API
title: Reg矢量计算接口软仿情况汇总
description: 本节汇总介绍了Reg矢量计算接口软仿数据类型的情况，本节内容仅针对如下型号生效：
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/reg_vector_compute_interface_soft_simulation_summary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: [agnostic]
---


# Reg矢量计算接口软仿情况汇总

本节汇总介绍了Reg矢量计算接口软仿数据类型的情况，本节内容仅针对如下型号生效： Ascend 950PR/Ascend 950DT Reg数据搬入和Reg数据搬出目录下提供了UB与RegTensor、UB与MaskReg之间的数据搬运接口。 UB与RegTensor之间的数据搬运根据操作数的数据类型位宽来搬运，与数据类型本身无关，表1和表2列出的软仿支持的数据类型包括以下情况： - 底层硬件不支持该数据类型，通过其他位宽相同的数据类型支持的搬运指令实现。 - 底层硬件不支持该数据类型，通过多种接口组合软仿实现。 - 底层硬件不支持该数据类型，通过双搬入 双搬出模式软仿实现RegTraitNumTwo的数据类型。
