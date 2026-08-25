---
type: Guide
title: 设置合理的L2 CacheMode
description: '>该性能优化指导适用于如下产品型号：'
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/memory_access/l2_cache_mode_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 设置合理的L2 CacheMode

【优先级】高
【描述】L2 Cache常用于缓存频繁访问的数据，其物理位置如下图所示：
L2 Cache的带宽相比GM的带宽有数倍的提升，因此当数据命中L2 Cache时，数据的搬运耗时会优化数倍。通常情况下，L2 Cache命中率越高，算子的性能越好，在实际访问中需要通过设置合理的L2 CacheMode来保证重复读取的数据尽量缓存在L2 Cache上。
## L2 Cache访问的原理及CacheMode介绍
数据通过MTE2搬运单元搬入时，L2 Cache访问的典型流程如下：
数据通过MTE3或者Fixpipe搬运单元搬出时，L2 Cache访问的典型流程如下：
从上面的流程可以看出，当数据访问总量超出L2 Cache容量时，AI Core会对L2 Cache进行数据替换。由于Cache一致性的要求，替换过程中旧数据需要先写回GM（此过程中会占用GM带宽），旧数据写回后，新的数据才能进入L2 Cache。
开发者可以针对访问的数据设置其CacheMode，对于只访问一次的Global Memory数据设置其访问状态为不进入L2 Cache，这样可以更加高效的利用L2 Cache缓存需要重复读取的数据，避免一次性访问的数据替换有效数据。
## 设置L2 CacheMode的方法
Ascend C基于GlobalTensor提供了SetL2CacheHint接口，用户可以根据需要指定CacheMode。
考虑如下场景，构造两个Tensor的相加计算，输入x、y和输出z的Shape均为(8192, 8192)。下文完整样例请参考设置合理L2 CacheMode样例。
