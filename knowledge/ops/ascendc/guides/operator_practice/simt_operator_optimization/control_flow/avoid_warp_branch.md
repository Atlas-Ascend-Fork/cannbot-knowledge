---
type: Guide
title: 同一Warp内避免分支跳转
description: 同一Warp内线程应避免分支跳转以防止分支发散，减少掩码屏蔽等待，提升SIMT算子执行效率。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simt_operator_optimization/control_flow/avoid_warp_branch.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 同一Warp内避免分支跳转

【优先级】高
【描述】SIMT编程模式下，Warp是基本的调度和执行单位，同一Warp内的32个线程执行同一条指令。流控制指令（if、switch、do、for、while）会产生分支跳转。当同一Warp内不同线程的跳转目标不一致时线程执行路径产生分歧，引起分支发散（Warp Divergence）。当发生分支发散时，只有进入当前分支的线程（活跃线程）正常执行，其余线程被掩码屏蔽等待，直至所有分支路径执行完毕后Warp内线程才能重新汇合。分支发散会增加Warp实际执行的指令总数，降低执行效率，严重影响算子性能。因此，同一Warp内的线程应尽量避免分支跳转。
在一个线程块内，所有线程按线性顺序被硬件自动划分为每32个线程一组的Warp，当控制流条件与线程ID有关时，应尽量保证同一Warp内的线程进入相同分支，减少分支发散。例如，对于一维线程块，当控制条件仅依赖于threadIdx.x / warpSize时，同一Warp内的线程走相同分支路径，无分支发散。
对于for循环等循环类控制流，应尽量使同一Warp内线程的循环次数保持一致，避免因循环次数不同产生较为严重的分支发散。当同一Warp内不同线程的循环次数不一致时，先退出循环的线程处于掩码屏蔽状态等待其余线程，直至Warp中最后一个线程完成循环，造成Warp内计算资源的严重浪费。
对于一些较为简单的分支，编译器可能通过谓词（Predication）优化避免产生分支跳转。此时，所有指令都会被执行，但其最终是否生效由每个线程的谓词决定。通过这种机制，可以减少分支跳转带来的性能损失。
【样例介绍】以SpMV Warp Divergence样例为例，样例中通过对比"一个线程处理一行数据"和"一个Warp协作处理一行数据"两种方式，展示Warp Divergence对性能的影响。该样例的功能为计算CSR格式存储的稀疏矩阵与稠密向量相乘。
稀疏矩阵是指大部分元素为零的矩阵。为了节省存储空间，稀疏矩阵通常采用CSR（Compressed Sparse Row）格式存储，仅保存非零元素及其位置信息。CSR格式使用3个数组：
- values：所有非零元素的值，按行优先顺序排列。
- col_idx：每个非零元素的列索引，与values一一对应。
- row_ptr：行偏移数组，记录每一行的非零元素在values数组中的起始和结束索引。例如，第i行的非零元素在values中的索引为[row_ptr[i], row_ptr[i+1])。
SpMV计算y = A * x，其中A为CSR格式稀疏矩阵，x为稠密向量，y为输出向量。
【反例】一个线程处理一行数据，同一Warp内线程的循环次数不一致，产生严重的Warp Divergence。
上述实现中，每个线程根据全局ID确定处理的行号，独立遍历该行的所有非零元素并累加乘积。同一Warp内32个线程处理32行，各行非零元素个数不同，循环次数从1到64不等。由于不同行的非零元素数量不同，同一Warp内的线程退出循环的时间不一致，产生严重的Warp Divergence。假设一个Warp中线程0处理的行非零元素个数为3，线程1处理的行非零元素个数为64，线程0在3次循环后进入空闲等待，而线程1需要执行64次循环。

<!-- cannbot:related:start -->
## 相关

- [AscShfl](../../../../apis/simt_api/warp_functions/warp_shfl_functions/asc_shfl.md)（`explains`）：AscShfl 与《同一Warp内避免分支跳转》的实质衔接是：AscShfl 与 up/down/xor 变体及 cooperative-group 对应入口共享 warp lane 交换契约，分支优化卡直接使用该类 warp 通信。
- [AscShflXor](../../../../apis/simt_api/warp_functions/warp_shfl_functions/asc_shfl_xor.md)（`explains`）：AscShflXor 与《同一Warp内避免分支跳转》的实质衔接是：AscShflXor 与 up/down/general 及 ShflXor 入口共享 warp lane 交换契约；同 warp 避免分支指南直接使用此类 shuffle 做数据重排。
- [Ballot](../../../../apis/simt_api/cooperative_groups/thread_block_tile/ballot.md)（`explains`）：Ballot 与《同一Warp内避免分支跳转》的实质衔接是：Ballot 把 thread_block_tile 各线程谓词压成位图；all/any、size、sync 与 tile 构造定义参与线程，warp vote 和分支优化说明结果的实际用途。
- [CoalescedGroup](../../../../apis/simt_api/cooperative_groups/coalesced_group/coalesced_group.md)（`explains`）：CoalescedGroup 与《同一Warp内避免分支跳转》的实质衔接是：CoalescedGroup 表示分支发散后当前 warp 的活跃子集；构造/简介、协作组总览、未 coalesce 故障和分支优化指南共同界定成员身份与适用场景。
- [Warp Shfl类函数](../../../../apis/simt_api/warp_functions/warp_shfl_functions/warp_shfl_functions.md)（`explains`）：Warp Shfl类函数 与《同一Warp内避免分支跳转》的实质衔接是：Warp Shfl 总览覆盖 general/down/up/xor 四种 lane 交换；coalesced/tile 对应入口和分支优化指南说明作用域及真实使用。
- [Warp Vote类函数](../../../../apis/simt_api/warp_functions/warp_vote_functions/warp_vote_functions.md)（`explains`）：Warp Vote类函数 与《同一Warp内避免分支跳转》的实质衔接是：该页自身仅列出 warp vote 成员，成员层级已由 part_of 表达；只保留直接使用 vote 做分支优化的指南及 cooperative-group Ballot 对照。
- [Warp函数](../../../../apis/simt_api/warp_functions/warp_functions.md)（`explains`）：Warp函数 与《同一Warp内避免分支跳转》的实质衔接是：Warp API 与 Warp 分支优化围绕同一 32-lane 执行和分歧成本，overview 提供成员之间的组合方式。
- [asc_any](../../../../apis/simt_api/warp_functions/warp_vote_functions/asc_any.md)（`explains`）：《asc_any》说明判断是否有活跃线程的输入不为0。 当Warp内所有活跃线程执行本接口后，对所有活跃线程的输入操作数predicate进行判断，所有活跃线程的predicate均为0，返回0，否则返回1。Warp内所有活跃线程返回相同的结果。；《同一Warp内避免分支跳转》说明同一Warp内线程应避免分支跳转以防止分支发散，减少掩码屏蔽等待，提升SIMT算子执行效率。。二者在asc_any对Warp活跃线程做投票，与all/ballot/activemask共同定义聚合谓词并影响分支收敛上存在可执行的直接衔接。
- [coalesced_group简介](../../../../apis/simt_api/cooperative_groups/coalesced_group/coalesced_group_intro.md)（`explains`）：coalesced_group简介 与《同一Warp内避免分支跳转》的实质衔接是：coalesced_group 表示 warp 当前活跃子集，构造、meta rank/size、thread rank、partition 与 coalesce 故障/分支指南共同界定发散后的成员身份。
- [AiCoreSimtProgrammingOverview](../../../programming_guide/programming_model/ai_core_simt_programming/overview.md)（`related`）：《同一Warp内避免分支跳转》的任务是“同一Warp内线程应避免分支跳转以防止分支发散，减少掩码屏蔽等待，提升SIMT算子执行效率。”。《AiCoreSimtProgrammingOverview》具体提供“SIMT编程模型适用于离散数据访问和复杂控制流场景，基于Grid-Block-Thread三级线程层级在AIV核上实现线程级并行计算。”，它直接用于Warp divergence 的线程架构、谓词/协作改写和优化总览。
- [SIMT算子优化概述](../overview.md)（`related`）：《同一Warp内避免分支跳转》的任务是“同一Warp内线程应避免分支跳转以防止分支发散，减少掩码屏蔽等待，提升SIMT算子执行效率。”。《SIMT算子优化概述》具体提供“SIMT编程模式以线程（Thread）为基本编程单位，由开发者编写单个线程的执行逻辑，再通过>>配置将大量线程组织为线程块（线程块）与线程网格（Grid），调度到硬件的Vector Core（物理核，即AIV核）上以Warp为单位并行执行。”，它直接用于Warp divergence 的线程架构、谓词/协作改写和优化总览。
- [ThreadArchitecture](../../../programming_guide/programming_model/ai_core_simt_programming/thread_architecture.md)（`related`）：《同一Warp内避免分支跳转》的任务是“同一Warp内线程应避免分支跳转以防止分支发散，减少掩码屏蔽等待，提升SIMT算子执行效率。”。《ThreadArchitecture》具体提供“SIMT编程模型采用Grid、Thread Block、Thread分层线程组织结构，每个层次维度可自定义配置，通过Warp调度机制执行。”，它直接用于Warp divergence 的线程架构、谓词/协作改写和优化总览。
- [通过SIMT实现分支判断](../../simd_simt_hybrid_optimization/compute_optimization/simt_branch_judgment.md)（`related`）：《同一Warp内避免分支跳转》的任务是“同一Warp内线程应避免分支跳转以防止分支发散，减少掩码屏蔽等待，提升SIMT算子执行效率。”。《通过SIMT实现分支判断》具体提供“>该性能优化建议适用于如下型号：”，它直接用于Warp divergence 的线程架构、谓词/协作改写和优化总览。
<!-- cannbot:related:end -->
