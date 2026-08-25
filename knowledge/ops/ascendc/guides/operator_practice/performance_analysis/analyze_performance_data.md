---
type: Guide
title: 分析性能数据（性能分析）
description: 理论性能为算子实际性能的理想目标。不同的硬件平台的硬件规格各异，理论性能可以帮助我们了解硬件的潜能，从而设定性能优化的目标。
tags: [task.lookup, topic.performance.analysis]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/performance_analysis/analyze_performance_data.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2]
---

# 分析性能数据

## 理论参数
理论性能为算子实际性能的理想目标。不同的硬件平台的硬件规格各异，理论性能可以帮助我们了解硬件的潜能，从而设定性能优化的目标。
-   搬运相关流水（MTE1/MTE2/MTE3等）的理论耗时 = 搬运数据量（单位：Byte） / 理论带宽。例如：某款AI处理器的GM峰值带宽约为1.8TB/s，想要进行一次float数据类型、4096 * 4096大小的矩阵搬运，搬运的理论耗时是sizeof(float) * 4096 * 4096 / 1.8TB/s = 37.28us（按照1TB =1012Byte来计算）。
-   计算相关流水（Cube/Vector/Scalar等）的理论耗时 = 计算数据量（单位：Element） / 理论算力。例如：某款AI处理器对float数据类型的Vector理论峰值算力为11.06TOPS，想要进行一次32K float类型的Element单指令计算，计算的理论耗时是32K / 11.06TOPS = 0.003us （按照1K =1000来计算）。
## 查找瓶颈
获取性能数据后，和理论数值差异较大的地方、耗时较长的流程被认为是“瓶颈点”。下文将介绍如何通过性能数据找到瓶颈点和对应的优化方向。
-   方法一：通过上板Profiling分析流水情况
查看上板Profiling解析后的op_summary_*.csv文件分析流水情况。注：“*”表示时间戳。
每条流水线的利用率理想情况下应为100%，没有达到100%的流水就可能有提升空间。上图示例中为某款AI处理器上获取的数据，可以看到Cube算子MatMulV2，Cube流水的利用率aic_mac_ratio在80%左右，初步判断没有充分发挥算力；MTE2流水的利用率aic_mte2_ratio已经在95%左右，判断MTE2是最长的流水。
然后比较最长的流水和理论的差距：输入左右矩阵的shape分别为（2048，12288）、（12288，6144），数据类型为bfloat16；Bias输入的shape为（6144），数据类型为float。由此可以计算出总共需要搬运的数据量，继而通过理论参数中介绍的搬运流水理论耗时计算方法计算出理论值为(sizeof(bfloat16) * (2048 * 12288 + 12288 * 6144) + sizeof(float) * 6144) / 1.8TB/s ≈ 111.8us （按照1TB =1012Byte来计算），与实际性能数据aic_mte2_time存在比较大的差距。经分析输入数据的总大小已经超过L1的空间（512KB），做MatMul计算会存在输入矩阵数据重复搬运的情况，重复搬运的次数是否合理，需要结合流水优化和Tiling优化手段进行优化，可参考方法三、查看仿真流水图分析各条流水的情况进一步分析。
上图示例中算子输入的shape为（8192，8192），数据类型为float。
