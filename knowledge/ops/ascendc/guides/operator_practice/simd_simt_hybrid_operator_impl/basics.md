---
type: Guide
title: 基础知识（SIMD与SIMT混合算子实现）
description: 本节内容为使用Reg矢量计算API和SIMT API进行SIMD与SIMT混合编程的指导。
tags: [task.lookup, topic.programming_model.development_mode.hybrid_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_simt_hybrid_operator_impl/basics.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 基础知识

本节内容为使用Reg矢量计算API和SIMT API进行SIMD与SIMT混合编程的指导。

在Vector Core中，SIMT单元和SIMD单元共享片上存储，因此可以利用片上存储Unified Buffer完成SIMD与SIMT混合编程，具体硬件架构的介绍请参考NPU架构版本3510。在进行后续内容的学习前，请先了解SIMD与SIMT混合编程的编程模型：SIMD与SIMT混合编程。

SIMD编程提供了基于寄存器（Regbase）开发的Reg矢量计算API，Reg矢量计算API可以直接操作Vector Core中的SIMD寄存器，API单次处理的数据量上限等于寄存器的大小，通过GetVecLen接口获取该值。在算子实现中，需要多次调用Reg矢量计算API完成对单核数据的处理。

与SIMD编程不同的是，在SIMT编程中Global Memory上的数据可以被直接读取和使用。SIMT编程常通过组织线程的层次结构来实现数据的切分，使用threadIdx等SIMT BuiltIn关键字计算线程应处理的数据索引，完成索引对应数据的计算，从而将函数实现简化为标量计算。

<!-- cannbot:related:start -->
## 相关

- [算子实现（SIMD与SIMT混合算子实现）](operator_impl.md)（`related`）：“SIMD编程提供了基于寄存器（Regbase）开发的Reg矢量计算API，Reg矢量计算API可以直接操作Vector Core中的SIMD寄存器，API单次处理的数据量上限等于寄存器的大小，通过GetVecLen接口获取该值。在算子实现中，需要多次调用Reg矢量计算API完成对单核数据的处理。”与“其中，gather阶段包含索引映射和离散访问，使用SIMT表达每个线程的数据访问逻辑；adds阶段处理连续数据，使用SIMD完成向量计算。”是双方正文中的具体合同。基础卡区分 SIMD 寄存器批处理与 SIMT 索引访问，实例卡把两种模式分别落到 gather 与 adds 阶段，能推进混合算子的阶段划分和实现。
<!-- cannbot:related:end -->
