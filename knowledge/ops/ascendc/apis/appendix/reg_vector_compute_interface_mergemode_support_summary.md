---
type: API
title: Reg矢量计算接口MergeMode支持情况汇总
description: 不支持MergeMode模板参数的接口，下文不罗列。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/reg_vector_compute_interface_mergemode_support_summary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Reg矢量计算接口MergeMode支持情况汇总

不支持MergeMode模板参数的接口，下文不罗列。

本接口属于 Reg 矢量计算接口，操作 RegTensor 寄存器数据。


临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
