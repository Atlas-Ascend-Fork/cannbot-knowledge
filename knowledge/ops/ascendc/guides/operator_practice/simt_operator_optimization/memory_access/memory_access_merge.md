---
type: Guide
title: MemoryAccessMerge
description: SIMT编程模式下让同一Warp内相邻线程访问连续GM地址以实现访存合并，提高GM带宽利用率。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simt_operator_optimization/memory_access/memory_access_merge.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 访存合并

【优先级】高
【描述】SIMT编程模式下，一个Warp内的相邻线程（thread）通常同时发起GM访问请求。若这些线程访问的GM地址连续，硬件可以将访问请求合并，从而提高GM带宽利用率；若相邻线程访问的GM地址跨行或离散分布，则难以形成访存合并，算子执行耗时会明显增加。对于转置、重排、gather/scatter等算子，需要结合数据排布和线程映射关系进行分析，尽量让同一个Warp内相邻线程在同一条访存指令上访问连续地址。
访存合并优化适用于两类场景：第一类是数据本身在GM上连续，只是相邻thread被分配处理的数据不连续，导致同一个Warp内相邻线程访问了不连续地址，此时优先调整数据切分方式，使Warp内相邻thread访问连续数据；第二类是算子功能包含转置、重排等布局变换，单纯调整切分方式很难同时保证GM读写都连续，此时考虑引入UB内存空间作为中转，利用UB完成不连续的数据重排过程，从而尽量保证GM侧访问连续。
- 优化数据切分实现访存合并
【样例介绍】以Gather算子为例，算子按行从输入中取数，计算公式可以表示为output[row, col] = input[index[row], col]。输出矩阵每一行内部的列方向数据在GM上连续，优化切分时应让同一个Warp内相邻线程尽量访问同一行内的相邻列，而不是只保证单个线程内部连续。
【反例】按thread切分数据，每个thread处理连续的一行数据。
上述实现把输出行分配给不同thread，每个thread在for循环内连续处理一整行数据。从单个thread视角看，input_idx和output_idx都是连续递增的；但SIMT访存合并的关键是同一个Warp内相邻thread在同一条访存指令上访问的地址连续。在该实现中，同一个Warp内的相邻thread分别处理不同的out_row，虽然单个thread内部访问连续，但Warp内访问不连续，GM访存难以合并。
以输入shape为20001×1023，index长度为核数乘以2048为例，线程块总数与物理核数相等，每个线程块启动2048个线程，反例算子执行该用例的性能数据如下：
Task Duration(us)：aiv_time(us)：aiv_total_cycles：aiv_vec_time(us)：aiv_vec_ratio：aiv_scalar_time(us)：aiv_scalar_ratio
4886.076：4535.644：7483813.083：4535.178：0.999：0.454：0.001
【正例】按Thread Block切分输出数据，Warp内相邻thread访问连续地址。
