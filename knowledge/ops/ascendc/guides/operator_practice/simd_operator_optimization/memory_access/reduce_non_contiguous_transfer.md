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

- [StoreAlignNoncontinuous](../../../../apis/simd_api/basic_api/reg_vector_compute/reg_data_store/store_align_noncontinuous.md)（`explains`）：StoreAlignNoncontinuous 与《非连续搬运场景减少搬运次数》的实质衔接是：StoreAlignNoncontinuous 按 DataBlock stride 将 RegTensor 写回 UB；连续/非对齐变体、LoadAlign 反向分布和非连续搬运指南共同决定布局、地址推进与搬运选择。
- [MulPreferContiguous 稀疏广播拦截失败且慢于 304](../../../../runbooks/performance/mulprefercontiguous_304.md)（`related`）：《MulPreferContiguous 稀疏广播拦截失败且慢于 304》处理“B 类稀疏广播（首轴稀疏、stride 大）触发 MulPreferContiguous 拦截转连续，baseline GetWorkspaceSize 返回 -1.0（schMode 空）或性能慢于 fixed 直接走 304 nddma_transpose_noLoop。”。《非连续搬运场景减少搬运次数》提供“>该性能优化建议适用于如下产品型号：”，其具体合同或探针直接接入稀疏广播输入的 contiguous 拦截、304 路由和非连续 shape/stride 合同。
- [尽量一次搬运较大的数据块](transfer_larger_data_blocks.md)（`related`）：先减少非连续片段再放大每次 block，二者共同降低 DMA 次数和启动开销。
- [跨行子块误作连续 slab 导致分块结果错](../../../../runbooks/precision/noncontiguous_row_subtiles_require_per_row_copy.md)（`related`）：指南提供非连续搬运的合并/二维 DMA 优化，但本卡给出跨行子块何时不能错误合并，二者共同限定优化安全边界。
- [非对齐场景减少无效数据的搬运](reduce_invalid_data_transfer.md)（`related`）：focal 用 Compact 减少非 32B 块的 padding 字节，目标用 Loop/NDDMA 减少非连续块的指令次数；两者分别优化搬运量和搬运次数，可按瓶颈组合。
- [EfficientTransferApi](efficient_transfer_api.md)（`same_topic`）：两篇指南都要求把非连续数据搬运编码为单次 DataCopy 参数，而非逐块循环调用；一篇给出 blockCount/blockLen/stride 原则，另一篇给出 DataCopyPad Loop 与 NDDMA 实例。
- [MemoryAccessMerge](../../simt_operator_optimization/memory_access/memory_access_merge.md)（`same_topic`）：《MemoryAccessMerge》处理“SIMT编程模式下让同一Warp内相邻线程访问连续GM地址以实现访存合并，提高GM带宽利用率。”。《非连续搬运场景减少搬运次数》提供“>该性能优化建议适用于如下产品型号：”，其具体合同或探针直接接入Warp 连续 GM 访问的短向量、类型对齐、步长搬运和 Gather 示例验证。
<!-- cannbot:related:end -->
