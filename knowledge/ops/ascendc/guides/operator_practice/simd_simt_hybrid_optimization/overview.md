---
type: Guide
title: SIMD与SIMT混合算子性能优化概述
description: AI Core上SIMD与SIMT混合编程结合了SIMD多数据并行计算能力与SIMT离散访存、复杂分支处理能力，可以在同一算子中以Vector
  Function（VF）为基本调度单位灵活组织SIMD和SIMT执行逻辑。SIMD编程适合处理连续、规整的向量或矩阵计算，SIMT编程适合处理分支判断、索引映射、离散访存等不规则逻辑，在程序中结合使用两种编程方式，可以兼顾硬件高吞吐和编程灵活性。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_simt_hybrid_optimization/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# SIMD与SIMT混合算子性能优化概述

AI Core上SIMD与SIMT混合编程结合了SIMD多数据并行计算能力与SIMT离散访存、复杂分支处理能力，可以在同一算子中以Vector Function（VF）为基本调度单位灵活组织SIMD和SIMT执行逻辑。SIMD编程适合处理连续、规整的向量或矩阵计算，SIMT编程适合处理分支判断、索引映射、离散访存等不规则逻辑，在程序中结合使用两种编程方式，可以兼顾硬件高吞吐和编程灵活性。
本节主要介绍SIMD与SIMT混合编程中SIMT VF的性能优化方法，帮助开发者基于性能数据判断SIMT VF片段的优化程度，并进一步选择合适的优化方向。优化时应先分析理论数据，再通过实际性能数据确认瓶颈，最后针对性地从内存访问、执行控制、指令优化等方面进行优化。
## 分析性能数据
性能分析的核心是先建立理论基准，再用实测数据观察当前实现与理论预期之间的差距。
1. 理论性能评估
理论性能评估用于建立算子的理想访存规模和设备GM（Global Memory）带宽上限。分析时应先根据算子语义、数据量和数据类型，估算算子完成一次计算所需的理论读数据量和理论写数据量，计算方式通常为访问元素个数乘以数据类型字节数。该数据量表示算法本身必须处理的数据规模，是后续判断实际读写是否合理的基准。在得到理论读写数据量后，还需要结合产品文档中的硬件规格获取设备GM理论带宽。理论带宽代表访存通路的理想上限，可用于评估当前算子实现的带宽利用水平和优化空间。
2. 实际数据度量
实际数据度量用于观察算子运行时的GM访问情况，以及SIMT VF在AIV核执行时间中的占比。可使用算子开发工具中的msOpProf工具采集性能数据：
- 通过Memory.csv查看AIV核整体GM读写带宽和读写数据量，相关性能数据字段为：aiv_main_mem_read_bw、aiv_main_mem_write_bw、read_main_memory_datas、write_main_memory_datas。
- 通过ArithmeticUtilization.csv查看算子在AIV核上的执行时间以及SIMT VF类型指令的cycle占比，相关性能数据字段为：aiv_time、aiv_vec_simt_vf_ratio。
在SIMD与SIMT混合编程中，aiv_time覆盖整个AIV核执行区间。分析SIMT VF自身性能时，应使用aiv_vec_simt_vf_ratio折算SIMT VF执行时间：
其中，aiv_vec_simt_vf_ratio表示SIMT VF类型指令cycle数占AIV核上执行的cycle总数的比例。
read_main_memory_datas和write_main_memory_datas是执行算子时的GM读、写数据量，未必全部是由SIMT VF触发的读写操作。计算SIMT VF实际带宽时，应使用SIMT VF相关GM读写数据量进行计算：
如果同一个Kernel中还存在SIMD VF、MTE搬运或其他阶段的GM读写，且无法判断GM读写数据是否由SIMT VF触发，则不应将AIV核整体GM读写量直接除以SIMT VF执行时间。
