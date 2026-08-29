---
type: Guide
title: 选择低延迟指令，优化归约操作性能
description: 指令执行延迟（Instruction Execution Latency）指的是一条指令从开始执行到完全完成（即所有操作结束，结果可用）所消耗的时间，它直接影响程序的响应速度和实时性。在延迟敏感的场景中，降低指令执行延迟是提升性能的关键。下文以归约操作为例，介绍了几种归约方案的性能对比，便于开发者在使用归约指令时，能够根据具体的数据规模和场景，选择性能更高的方案。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/vector_compute/low_latency_instruction.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 选择低延迟指令，优化归约操作性能

【优先级】高
【描述】
指令执行延迟（Instruction Execution Latency）指的是一条指令从开始执行到完全完成（即所有操作结束，结果可用）所消耗的时间，它直接影响程序的响应速度和实时性。在延迟敏感的场景中，降低指令执行延迟是提升性能的关键。下文以归约操作为例，介绍了几种归约方案的性能对比，便于开发者在使用归约指令时，能够根据具体的数据规模和场景，选择性能更高的方案。
## 二分累加方案和归约类指令方案的对比
根据单指令性能测试数据（开发者可以自行测试）分析，ReduceRepeat等归约指令的延迟时间约为Add指令的2-5倍。因此，对于连续数据的归约操作，可以采用Add指令和ReduceRepeat指令的组合，以优化整体性能。该方案简称为二分累加方案，具体方案说明如下：
-   二分累加：将数据一分为二，使用Add指令将两部分数据相加；将相加后的结果再次一分为二，继续使用Add指令进行累加，重复此过程。
-   当二分累加后的数据量小于等于256Byte（一条指令一个Repeat的数据操作量），使用ReduceRepeat指令，一次执行得到归约结果。
假设输入数据的数据类型为float，shape为(5, 256)，下图展示了一行数据的执行过程：
将以上过程，针对每一行，各自执行，得到最终归约结果，即shape为(m, k)的数据，归约完成后，shape为(m, 1)。
由于ReduceSum接口是由多种指令组合实现，通常来说，数据量较大，循环次数较多的场景，二分累加方案性能 > ReduceRepeat单指令操作性能 > ReduceSum接口性能。而小数据量或者特殊shape下的场景，需要拆分开来，依据指令执行时间和指令执行数目等条件，具体问题具体分析。
下文给出了二分累加方案和归约类指令方案的核心代码片段和性能数据对比。完整样例请参考ReduceCustom。
【性能数据】
输入shape为30000，数据类型为float时，如下示例的性能数据对比如下，数据单位为cycle，使用GetSystemCycle接口获取。
【二分累加方案】
【ReduceRepeat单指令操作】
## ReduceDataBlock和ReduceRepeat归约方案对比
进一步测试分析可知，单指令ReduceDataBlock的执行效率优于ReduceRepeat，因此，根据不同的shape，通过不同的指令组合，可以达到更佳的执行性能。
例如数据类型为float，shape大小为256的数据，可以通过如下三种方式得到归约结果：
-   使用两次ReduceRepeat；
-   使用三次ReduceDataBlock；
-   一次ReduceDataBlock操作加一次ReduceRepeat操作。
通过分析单指令性能数据（开发者可以自行测试）可知：一次ReduceDataBlock操作加一次ReduceRepeat操作性能优于两次ReduceRepeat，同时也优于三次ReduceDataBlock的方案。
下文给出了上面三种方式的核心代码片段和性能数据对比。完整样例请参考ReduceCustom。
【性能数据】
输入shape为256，数据类型为float。

<!-- cannbot:related:start -->
## 相关

- [GetSystemCycle](../../../../apis/simd_api/basic_api/tool_interface/system_resources_and_variables/get_system_cycle_isasi.md)（`explains`）：“输入shape为30000，数据类型为float时，如下示例的性能数据对比如下，数据单位为cycle，使用GetSystemCycle接口获取。”；“获取系统计数器当前的cycle值。通过计算代码段前后cycle值的差值，可得到代码段消耗的系统cycle数，再通过换算即可获得代码段的执行时间。”。GetSystemCycle 是指南中比较归约方案 cycle 的直接测量接口，并给出平台频率换算合同。
- [ReduceDataBlock](../../../../apis/simd_api/basic_api/memory_vector_compute/reduction_compute/reduce_data_block.md)（`explains`）：“进一步测试分析可知，单指令ReduceDataBlock的执行效率优于ReduceRepeat，因此，根据不同的shape，通过不同的指令组合，可以达到更佳的执行性能。”；“对输入数据以DataBlock为单位进行归约操作，根据reduceType对每个DataBlock内数据求和、求最大值或求最小值。”。指南明确用 ReduceDataBlock 与 ReduceRepeat 的组合选择降低归约延迟，接口卡界定 DataBlock 级计算。
- [ReduceRepeat](../../../../apis/simd_api/basic_api/memory_vector_compute/reduction_compute/reduce_repeat.md)（`explains`）：“当二分累加后的数据量小于等于256Byte（一条指令一个Repeat的数据操作量），使用ReduceRepeat指令，一次执行得到归约结果。”；“对每个repeat内所有数据进行归约操作，支持求和、求最大值和求最小值，可返回最值索引。”。指南给出 ReduceRepeat 在二分累加尾段的具体选用条件，接口卡提供该调用的归约语义。
<!-- cannbot:related:end -->
