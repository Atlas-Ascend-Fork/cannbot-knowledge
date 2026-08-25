---
type: Guide
title: 通过SIMT实现分支判断
description: '>该性能优化建议适用于如下型号：'
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_simt_hybrid_optimization/compute_optimization/simt_branch_judgment.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# 通过SIMT实现分支判断

【优先级】高
【描述】基于SIMD编程模型实现的批量数据计算性能很高，但在算子实现逻辑中涉及分支判断时，基于SIMD的计算操作会变得相对复杂，导致性能下降。此时，可以考虑采用SIMT方式，因为SIMT编程更为灵活，更适合处理分支判断的场景。
【样例介绍】以floor_mod算子为例，算子功能为将输入x的每个元素除以输入y的对应元素，获取余数。该余数应与除数y具有相同的符号，且其绝对值应小于y的绝对值。在计算过程中，需要判断y中每个元素的符号以及余数与该元素绝对值的大小关系。完整的算子实现代码请参考SIMT与SIMD混合编程高性能优化样例。
样例规格
SIMT线程层次结构为：
-   Kernel启动核数：64
-   单次SIMT VF调用线程数：1024
【反例】
基于SIMD Reg矢量计算的floor_mod算子实现：对应样例中的场景1（SCENARIO_NUM=1）。该场景使用 asc_copy_gm2ub_align 和 asc_copy_ub2gm_align 完成GM与UB之间的数据搬运，在UB上使用SIMD VF函数实现计算。由于SIMD无法直接通过普通if else语句表达逐元素分支判断，因此需要使用多个矢量计算API完成符号比较、条件组合和结果选择，相关代码如下。
【正例】
基于SIMT的floor_mod算子实现：对应样例中的场景3（SCENARIO_NUM=3）。该场景同样使用搬运接口完成GM与UB之间的数据搬运，在UB上采用SIMT编程方式实现计算过程，通过if else语句完成分支判断，代码如下所示。
【性能对比】
在核数相同、输入输出规格相同、均使用搬运接口完成GM与UB之间数据搬运的情况下，对比场景1和场景3的性能数据如下。
除Task Duration外，其余指标均为所有Thread Block上的平均值。
场景：实现方式：核数：Task Duration(μs)：aiv_vec_time(μs)：aiv_vec_ratio：aiv_mte2_time(μs)：aiv_mte2_ratio
场景1：SIMD Reg矢量计算：64：525.736：509.987：0.989：217.341：0.421
场景3：SIMT连续访问UB：64：463.179：301.474：0.668：437.055：0.968
相比场景1，场景3使用SIMT直接表达floor_mod中的分支判断逻辑，aiv_vec_time从509.987μs降低至301.474μs，下降约40.9%，说明Vector计算侧耗时明显降低。端到端Task Duration从525.736μs降低至463.179μs，下降约11.9%，场景3的aiv_mte2_ratio达到0.968，主要瓶颈已转为MTE2 Bound，即算子性能的最大影响转变为GM到UB的搬运效率。

<!-- cannbot:related:start -->
## 相关

- [SimdSimtHybridProgrammingIntro](../../../../apis/simt_api/simd_simt_hybrid_programming_intro/simd_simt_hybrid_programming_intro.md)（`explains`）：《SimdSimtHybridProgrammingIntro》明确“SIMD与SIMT混合编程简介，包含编程模型、扩展语法和API列表导航。”；它与《通过SIMT实现分支判断》的“>该性能优化建议适用于如下型号：”在实际调用参数、数据流或结果校验上直接衔接。
- [SIMD与SIMT混合编程概述](../../../programming_guide/advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/overview.md)（`related`）：通过SIMT实现分支判断说明>该性能优化建议适用于如下型号：。
- [同一Warp内避免分支跳转](../../simt_operator_optimization/control_flow/avoid_warp_branch.md)（`related`）：《同一Warp内避免分支跳转》的任务是“同一Warp内线程应避免分支跳转以防止分支发散，减少掩码屏蔽等待，提升SIMT算子执行效率。”。《通过SIMT实现分支判断》具体提供“>该性能优化建议适用于如下型号：”，它直接用于Warp divergence 的线程架构、谓词/协作改写和优化总览。
- [抽象硬件架构（SIMD与SIMT混合编程）](../../../programming_guide/advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/abstract_hardware_architecture.md)（`related`）：通过SIMT实现分支判断说明>该性能优化建议适用于如下型号：；对抽象硬件架构（SIMD与SIMT混合编程）而言，混合编程概述定义 SIMD/SIMT 分工，性能章节给出分支与访存选择，SIMT 分支实现卡提供落地接口。
<!-- cannbot:related:end -->
