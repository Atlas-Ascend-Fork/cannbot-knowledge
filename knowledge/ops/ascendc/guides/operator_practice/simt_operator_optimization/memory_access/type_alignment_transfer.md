---
type: Guide
title: 通过类型对齐提升搬运效率
description: 【描述】SIMT编程模式下，结构体类型对齐会影响Global Memory的访存效率。在数据总量不变时，可通过类型对齐到更大的位宽，提升数据搬运效率。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simt_operator_optimization/memory_access/type_alignment_transfer.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 通过类型对齐提升搬运效率

【优先级】中
【描述】SIMT编程模式下，结构体类型对齐会影响Global Memory的访存效率。在数据总量不变时，可通过类型对齐到更大的位宽，提升数据搬运效率。
【样例介绍】设置总搬运量MEM_BYTES为512MiB，构造多组不同大小、不同对齐方式的结构体TData，依次将长度为num_elements的输入数组d_idata整体复制到输出数组d_odata进行测试，对比非对齐与使用alignas类型对齐后的耗时差异。具体代码可参考类型对齐优化搬运效率最佳实践样例，其中核函数实现如下：
下面以Align4、Misalign4这两个结构体作为典型代表展示对照场景。
【反例】Misalign4未设置显式对齐，默认alignof受字段类型限制，编译器只能选用窄位宽的访存指令。
性能数据如下：
Task Duration(us)：aiv_total_cycles
81223.02：134028903.60
上述结构体由字段类型决定alignof=1，编译器只能用8-bit档位搬运每个元素，aiv_total_cycles和Task Duration都较高。
【正例】使用alignas提升对齐属性，编译器可以选用更宽位宽的访存指令。
性能数据如下：
Task Duration(us)：aiv_total_cycles
27889.33：46005213.32
Align4将alignof从1B提升到4B，编译器可以选用32-bit档位完成单元素搬运，aiv_total_cycles和Task Duration都显著减小。
