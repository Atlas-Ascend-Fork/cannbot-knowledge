---
type: Guide
title: 非对齐场景减少无效数据的搬运
description: '>该性能优化建议适用于如下型号：'
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/memory_access/reduce_invalid_data_transfer.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 非对齐场景减少无效数据的搬运

【优先级】中
【描述】在非对齐数据搬运场景中，Ascend 950PR/Ascend 950DT在基础API层面提供了DataCopyPad接口，该接口支持Normal、Compact（紧凑）两种搬运模式。搬运多块非32B对齐数据块的场景下，使用Compact模式在可以减少搬运的无效数据量，节省带宽。
假设需要搬运三个数据块，每块数据块大小为48B，数据类型为float类型。除了这三个48字节的数据块之外，其他所有数据均为无效数据。
【反例】使用DataCopyPad接口进行Normal模式搬运数据
搬运后UB内数据如下：
如图所示，由于每块数据块为48B，非32B对齐，因此搬运每块数据块时需要插入16B大小的padding数据使得数据32B对齐，最终搬运192B大小的数据到UB，其中包含48B的无效数据。
【正例】改用Compact模式搬运进行优化
搬运后UB内数据如下：
根据Compact模式搬运的示意图，最终搬运了160B大小的数据，其中包含16B的无效数据。
【总结】通过比较可以发现，搬运多块非32B对齐数据块的场景下，使用Compact模式在可以减少搬运的无效数据量，节省带宽。
