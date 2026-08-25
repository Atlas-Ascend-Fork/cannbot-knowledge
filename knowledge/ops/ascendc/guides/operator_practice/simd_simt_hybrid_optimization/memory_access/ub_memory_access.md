---
type: Guide
title: 使用Unified Buffer提升内存访问效率
description: '>该性能优化建议适用于如下型号：'
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_simt_hybrid_optimization/memory_access/ub_memory_access.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# 使用Unified Buffer提升内存访问效率

【优先级】高
【描述】SIMT线程直接访问Global Memory时，访存请求会经过GM访问路径，数据搬运和线程计算耦合在同一段SIMT逻辑中，容易降低整体访存效率。当单次处理的数据量可放入最大可用Unified Buffer空间（256KB - 系统预留8KB - 最小Dcache 32KB）时，可以使用搬运接口将数据从Global Memory连续搬运到Unified Buffer，使SIMT编程直接访问Unified Buffer中的数据，从而提高内存访问效率，提升算子的整体性能。
【样例介绍】以SIMD与SIMT混合编程方式实现的floor_mod算子为例。该算子输入x和y的shape均为[8192, 8192]，数据类型为int32，输出z的shape为[8192, 8192]。完整样例请参考SIMT与SIMD混合编程高性能优化样例。
样例规格
SIMT线程层次结构为：
-   Kernel启动核数：64
-   单次SIMT VF调用线程数：1024
【反例】
SIMT直接访问Global Memory上的x、y和z数据，对应样例中的场景0（SCENARIO_NUM=0）。该场景未通过MTE完成GM与UB之间的数据搬运，SIMT线程直接从GM读取输入并将结果写回GM，代码如下。
【正例】
使用搬运接口将x和y从Global Memory连续搬运到Unified Buffer，基于SIMT编程方式直接从Unified Buffer读取数据并写入Unified Buffer，再将结果连续写回Global Memory，对应样例中的场景3（SCENARIO_NUM=3）。该实现采用ping-pong双缓冲策略，通过两组UB缓冲区交替处理数据，使MTE2搬入流水、Vector计算流水和MTE3搬出流水并行执行。代码如下。
【性能对比】
场景0和场景3的性能对比如下。
除Task Duration外，其余指标均为所有Thread Block上的平均值。
场景：实现方式：核数：Task Duration(μs)：aiv_vec_time(μs)：aiv_mte2_time(μs)：aiv_mte3_time(μs)
场景0：SIMT直接访问GM：64：812.063：785.715：0.004：0.001
场景3：SIMT连续访问UB：64：463.179：301.474：437.055：110.788
场景0中，aiv_mte2_time和aiv_mte3_time接近0，说明数据读写没有走GM到UB、UB到GM的MTE搬运路径，耗时主要集中在SIMT直接访问GM和计算过程上。场景3中，输入和输出通过搬运接口在GM与UB之间连续搬运，SIMT线程直接访问UB完成计算，Task Duration从812.063μs降低至463.179μs，端到端耗时下降约43.0%。

<!-- cannbot:related:start -->
## 相关

- [SIMD与SIMT混合算子性能优化概述](../overview.md)（`related`）：《SIMD与SIMT混合算子性能优化概述》明确“AI Core上SIMD与SIMT混合编程结合了SIMD多数据并行计算能力与SIMT离散访存、复杂分支处理能力，可以在同一算子中以Vector Function（VF）为基本调度单位灵活组织SIMD和SIMT执行逻辑。SIMD编程适合处理连续、规整的向量或矩阵计算，SIMT编程适合处理分支判断、索引映射、离散访存等不规则逻辑，在程序中结合使用两种编程方式，可以兼顾硬件高吞吐和编程灵活性。”；它与《使用Unified Buffer提升内存访问效率》的“>该性能优化建议适用于如下型号：”在实际调用参数、数据流或结果校验上直接衔接。
- [内存层级（SIMD与SIMT混合编程）](../../../programming_guide/advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/memory_hierarchy.md)（`related`）：《内存层级（SIMD与SIMT混合编程）》给出“在SIMD与SIMT混合编程场景下，整体内存资源如下图所示。核外的Global Memory是所有核的全局内存，容量最大，但访问效率最低。AIC的L1和AIV的UB是单核内的共享内存，容量较小，但访问效率较高。私有内存层最靠近计算单元，容量最小，访问效率最高。”；该约束/探针可直接复现、解释或前置验证《使用Unified Buffer提升内存访问效率》中的“>该性能优化建议适用于如下型号：”。
- [算子实现（SIMD与SIMT混合算子实现）](../../simd_simt_hybrid_operator_impl/operator_impl.md)（`related`）：《算子实现（SIMD与SIMT混合算子实现）》给出“以下内容以gather & adds算子为例，介绍SIMD与SIMT混合算子的实现过程。完整代码请参见SIMD与SIMT混合编程实现gather&adds算子样例。”；该约束/探针可直接复现、解释或前置验证《使用Unified Buffer提升内存访问效率》中的“>该性能优化建议适用于如下型号：”。
<!-- cannbot:related:end -->
