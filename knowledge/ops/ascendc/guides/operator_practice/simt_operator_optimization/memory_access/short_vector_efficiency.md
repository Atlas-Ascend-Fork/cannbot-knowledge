---
type: Guide
title: ShortVectorEfficiency
description: SIMT编程模式下使用短向量类型替代普通数据类型进行数据搬运和计算，覆盖整个Cache Line，提升访存效率。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simt_operator_optimization/memory_access/short_vector_efficiency.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 使用短向量类型提升效率

【优先级】中
【描述】SIMT编程模式下，使用短向量类型替代普通数据类型以提升算子执行效率。AI处理器以Cache Line为128字节访问L2 Cache，当处理内存占用两字节的数据类型时，单个Warp对连续数据进行合并访存的有效数据量仅为64字节，未达到单个Cache Line的数据长度，带宽利用率为50%。通过使用短向量类型进行数据搬运和计算，每个Warp内线程的单次合并访存可覆盖整个Cache Line，利用100%的带宽，显著提升整体访存效率。
【样例介绍】以向量加法算子为例，输入数据为half类型，计算公式为 $z_i = x_i + y_i$。数据规模为64×256×1024个元素，算子内配置64个线程块、每个线程块内1024个线程，总线程数65536，每个线程处理256个元素。相同配置下，使用half2短向量类型处理输入数据，每个线程处理128个元素。
【反例】使用half类型逐元素计算，Cache Line占用不满。
在上述实现中，由于采用标量half（2B）数据类型，单个Warp（32线程）合并访存所生成的物理连续地址请求宽度仅为64B，128B的Cache Line未被完全占用。
在Ascend 950PR产品上，该实现的性能数据如下：
Task Duration(μs)：aiv_time(μs)：aiv_total_cycles：aiv_vec_time(μs)：aiv_vec_ratio：aiv_scalar_time(μs)：aiv_scalar_ratio：aiv_read_hit_rate：aiv_write_hit_rate：aiv_main_mem_read_bw(GB/s)：aiv_main_mem_write_bw(GB/s)
86.478：86.217：8832432：85.735：0.995：0.47：0.005：0：0.493：7.77：6.24
从性能数据可以看出，读带宽为7.77 GB/s，写带宽为6.24 GB/s。
【正例】使用half2类型计算，提升带宽利用率。

<!-- cannbot:related:start -->
## 相关

- [DCacheAccess](dcache_access.md)（`related`）：短向量能让一次搬运覆盖更多连续字节/Cache Line，与 DCache 策略组合可减少事务数并提升热点访问吞吐。
- [通过类型对齐提升搬运效率](type_alignment_transfer.md)（`related`）：ShortVector 用 half2 等短向量把 Warp 单次有效宽度扩到 128B Cache Line，与 alignas 扩大结构体访问位宽属于同一事务宽度优化链。
- [MemoryAccessMerge](memory_access_merge.md)（`same_topic`）：《MemoryAccessMerge》处理“SIMT编程模式下让同一Warp内相邻线程访问连续GM地址以实现访存合并，提高GM带宽利用率。”。《ShortVectorEfficiency》提供“SIMT编程模式下使用短向量类型替代普通数据类型进行数据搬运和计算，覆盖整个Cache Line，提升访存效率。”，其具体合同或探针直接接入Warp 连续 GM 访问的短向量、类型对齐、步长搬运和 Gather 示例验证。
<!-- cannbot:related:end -->
