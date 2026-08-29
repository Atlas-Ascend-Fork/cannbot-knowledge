---
type: API
title: 通用说明和约束（SIMD API）
description: 说明 SIMD 基础与高阶 API 的头文件、链接方式、存储单元对齐要求及 TPosition 内存映射。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/general_description_and_constraints.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 通用说明和约束（SIMD API）

Ascend C基础API和高阶API均支持通过包含kernel_operator.h文件来调用相应接口。基础API头文件目录为asc/include/basic_api，高阶API头文件目录为asc/include/adv_api和asc/include/tiling。高阶API因配套Host Tiling接口需链接libtiling_api.a。

约束：AI Core上的存储单元用于存储矢量计算、矩阵计算的源操作数和目的操作数，各类存储单元的对齐要求如下：Global Memory无对齐要求；Unified Buffer需32Byte对齐；L1 Buffer需32Byte对齐。如果接口中已明确说明操作数起始地址对齐要求，则以具体API中的说明为准。

TPosition逻辑位置与物理内存映射：GM对应Global Memory，VECIN/VECCALC/VECOUT对应Unified Buffer，A1/B1对应L1 Buffer，A2对应L0A Buffer，B2对应L0B Buffer，CO1对应L0C Buffer。
