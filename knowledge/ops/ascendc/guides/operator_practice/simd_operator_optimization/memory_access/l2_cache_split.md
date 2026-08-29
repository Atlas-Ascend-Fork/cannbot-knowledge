---
type: Guide
title: L2CacheSplit
description: 当输入和输出数据量超过L2 Cache大小时，在Tiling中开启L2 Cache切分策略以提升带宽利用效率。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/memory_access/l2_cache_split.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# L2 Cache切分

【优先级】：高
【描述】假设，AI处理器的L2 Cache大小为192MB，L2 Cache读写混合带宽约为7TB/s，而GM的带宽约为1.6TB/s，两者之间存在较大差距。搬入或搬出相同数据量的情况下，访问L2 Cache读写数据比GM更快。若数据无法命中L2 Cache，即需要访问的数据不在L2 Cache内，导致需要去GM上读写，带宽利用效率较低，最终算子搬入或搬出数据变为算子整个运行过程的性能瓶颈。切分策略建议：当输入和输出数据的数据量超过L2 Cache大小时，Tiling中开启L2 Cache切分策略。
【反例】
假设输入数据大小为InputTotalSize，L2 Cache大小为L2CacheSize，InputTotalSize = L2CacheSize * 2，总核数为20个核，数据未切分，整体一次完成计算。假设20个核一次可以处理共L2CacheSize的数据，则每个核至少两次读取输入数据。
【正例】
假设输入数据大小为InputTotalSize，L2 Cache大小为L2CacheSize，InputTotalSize = L2CacheSize * 2，能使用的总核数为20个核，输入数据均等切分成2份数据，则整体分两次进行计算，每次的计算量为L2CacheSize，第一次20个核先计算前L2CacheSize个数据，第二次20个核计算后L2CacheSize个数据。每次计算前读取的数据能够命中L2 Cache，提升算子性能。
更多完整样例请参考L2 Cache切分的算子样例。

<!-- cannbot:related:start -->
## 相关

- [Matmul高阶API开启L2 Cache切分](../../best_practices/matmul_tuning_cases/matmul_l2_cache_split.md)（`same_topic`）：Matmul 案例的适用条件是“输入和输出的数据量超过L2 Cache的大小。”；通用指南给出决策“当输入和输出数据的数据量超过L2 Cache大小时，Tiling中开启L2 Cache切分策略。”。两卡围绕同一切分决策，案例进一步给出 Matmul 分块与拖尾选法。
<!-- cannbot:related:end -->
