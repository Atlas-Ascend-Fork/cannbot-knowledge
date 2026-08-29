---
type: Guide
title: 非连续搬运场景减少搬运次数
description: '>该性能优化建议适用于如下产品型号：'
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/memory_access/reduce_non_contiguous_transfer.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 非连续搬运场景减少搬运次数

【优先级】中
在非连续搬运场景可以使用DataCopyPad接口的Loop模式和DataCopy的多维数据搬运接口来减少搬运次数，优化搬运性能。
## 使用Loop模式减少非连续搬运的次数
【描述】DataCopyPad接口在Normal/Compact模式基础上，可以使用Loop模式搬运二维数据，假设我们希望以下图的方式搬运8个48B大小的数据块：
【反例】调用多次搬运接口进行搬运（以DataCopyPad为例）
【正例】使用Loop模式进行搬运
【总结】当数据块之间需要插入不同大小Padding时，使用Loop模式搬运代替多次的DataCopyPad能够减少搬运指令的使用，提升性能。
## 使用多维数据搬运减少非连续搬运次数
【描述】假设我们希望以下图的方式搬运2个8B大小的数据块：
【反例】使用多次DataCopyPad进行搬运
【正例】使用多维数据搬运
DataCopy接口在Ascend 950PR/Ascend 950DT上支持多维数据的搬运，具体可参考DataCopy（GMToUB多维数据搬运NDDMA）。以2D场景的搬运为例，代码如下：
【总结】使用多维数据搬运在部分场景下能够减少搬运指令的条数，从而提升性能。

<!-- cannbot:related:start -->
## 相关

- [跨行子块误作连续 slab 导致分块结果错](../../../../runbooks/precision/noncontiguous_row_subtiles_require_per_row_copy.md)（`related`）：在非连续搬运场景可以使用DataCopyPad接口的Loop模式和DataCopy的多维数据搬运接口来减少搬运次数，优化搬运性能。；- `nCur < N_` 改用逐行 DMA，放弃未核实字段语义的 2D `srcStride` 一次搬运，优先保证正确性；指南给出非连续二维块在已核实参数下减少搬运指令的优化路径，运行手册给出行宽小于物理步长时先按行搬运的正确性基线，二者共同指导先证明 stride 合同再选择批量搬运。
<!-- cannbot:related:end -->
