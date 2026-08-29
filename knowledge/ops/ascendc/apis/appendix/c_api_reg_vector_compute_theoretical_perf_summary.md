---
type: API
title: C-API-Reg矢量计算接口理论性能汇总
description: 本节汇总介绍了C-API Reg矢量计算接口的理论性能，本节内容仅针对如下型号生效：
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/c_api_reg_vector_compute_theoretical_perf_summary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# C-API-Reg矢量计算接口理论性能汇总

本节汇总介绍了C-API Reg矢量计算接口的理论性能，本节内容仅针对如下型号生效：

本接口属于 Reg 矢量计算接口，操作 RegTensor 寄存器数据。


临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
