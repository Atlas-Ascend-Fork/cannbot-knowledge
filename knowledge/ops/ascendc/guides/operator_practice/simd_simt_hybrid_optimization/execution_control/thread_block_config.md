---
type: Guide
title: 线程块数量配置优化
description: '>该性能优化建议适用于如下型号：'
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_simt_hybrid_optimization/execution_control/thread_block_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 线程块数量配置优化

【优先级】高
【描述】SIMT kernel启动时，通过核函数调用符>>的第一个参数配置本次任务要启动的线程块数量，这些线程块需要在硬件实际存在的Vector Core（物理核）上执行。由于硬件限制，一个物理核同一时刻只能驻留并执行一个线程块，每个线程块的启动和调度都会引入固定开销。当线程块数量不超过物理核数时，所有线程块可以一次占满物理核并行执行；当线程块数量超过物理核数时，超出的线程块必须等待物理核空闲后才能被调度，调度开销随超出的线程块数量近似线性增加。因此，线程块数量应结合物理核数与数据规模设置。
物理核数可以在运行期通过aclrtGetDeviceInfo查询。在下面的场景中，实测的物理核数均为64。
确定物理核数后，还需结合数据规模来设置线程块数量。
大数据量下，线程块数量应等于物理核数。线程块数量过多会导致超出物理核数的线程块排队等待，耗时增加；线程块数量过少会导致物理核闲置、并行核数不足、单核工作量增加，并显著影响耗时。
小数据量下，每核工作量较小，启动更多核带来的调度头开销可能会反超有效并行计算的收益，最优核数往往小于物理核数。
此外，当每核实际处理的元素数小于2048时，线程数量应按每核实际处理的元素数分配，避免空转线程浪费性能。
【样例介绍】以Gather算子为例，算子功能为根据索引张量从输入张量中采集对应位置的数据写入输出，计算公式为output[i][j] = input[index[i][j]]。完整样例请参考线程块数量配置与vf调用优化样例。
【反例】
反例1：大数据量下线程块数量远超物理核数
以Gather算子大数据量（index和output形状为[1024, 2048]）为例。该场景通过>>启动1024个线程块，远超物理核数，超出的线程块必须排队等待物理核空闲后才能被调度，代码示例如下：
反例2：大数据量下线程块数量低于物理核数
同一大数据量下。该场景通过>>启动32个线程块，线程块数量仅为物理核数的一半，并行度不足，每个线程块处理的工作量翻倍，代码示例如下：
反例3：小数据量下线程块数量等于物理核数
以Gather算子小数据量（index和output形状为[8, 2048]）为例。该场景通过>>启动64个线程块（等于物理核数），但每核仅处理256个元素，增加核数带来的调度开销反超并行收益，代码示例如下：
【正例】
正例1：大数据量下线程块数量等于物理核数
大数据量下通过>>启动64个线程块（等于物理核数），所有线程块一次占满物理核并行执行，无需排队等待，并行度充足。代码示例如下：
正例2：小数据量下实测最优核数且线程数量按实际元素数分配
小数据量下通过实测性能数据得到最优核数为32。

<!-- cannbot:related:start -->
## 相关

- [block 数应覆盖可用 Vector 核](../../../../runbooks/performance/block_count_uses_all_available_vector_cores.md)（`related`）：指南给出“大 workload 时 block 数等于实测物理 Vector Core、小时应降低”的选择规则；Runbook 在 A3 上把固定 32 上限改为 `min(N_out,V_measured)`，以 20/20 正确性和整体时间比 0.758 验证了同一大 workload 决策。
- [线程块数量配置优化](../../simt_operator_optimization/execution_config/thread_block_config.md)（`same_topic`）：两张指南处理同一个线程块数量决策：大数据量让 block 数匹配物理 Vector Core，小数据量因固定调度开销需实测较小最优值，并通过 `aclrtGetDeviceInfo` 获取物理核数；区别只是混合编程与纯 SIMT 章节切面。
<!-- cannbot:related:end -->
