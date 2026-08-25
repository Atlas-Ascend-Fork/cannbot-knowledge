---
type: Guide
title: 尽量一次搬运较大的数据块
description: 【描述】搬运不同大小的数据块时，对带宽的利用率（有效带宽/理论带宽）不一样。根据实测经验，单次搬运数据长度16KB以上时，通常能较好地发挥出带宽的最佳性能。因此对于单次搬运，应考虑尽可能的搬运较大的数据块。下图展示了某款AI处理器上实测的不同搬运数据量下带宽的变化图。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/memory_access/transfer_larger_data_blocks.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 尽量一次搬运较大的数据块

【优先级】高

【描述】搬运不同大小的数据块时，对带宽的利用率（有效带宽/理论带宽）不一样。根据实测经验，单次搬运数据长度16KB以上时，通常能较好地发挥出带宽的最佳性能。因此对于单次搬运，应考虑尽可能的搬运较大的数据块。下图展示了某款AI处理器上实测的不同搬运数据量下带宽的变化图。

>测试数据与处理器型号相关，且实际测试时可能会存在略微抖动，具体带宽数值并不一定和下文的测试数据严格一致。

**图1**  UB->GM方向不同单次搬运数据量下实际占用带宽的变化

**图2**  GM->UB方向不同单次搬运数据量下实际占用带宽的变化

<!-- cannbot:related:start -->
## 相关

- [EfficientTransferApi](efficient_transfer_api.md)（`related`）：高效搬运接口页提供合并连续 block 所需的 DataCopy/NDDMA 选型与参数。
- [GM地址尽量512B对齐](gm_address_512b_alignment.md)（`related`）：在基址对齐之外，单次搬运块达到约 16KB 才能进一步提高有效带宽，补足地址与长度两个独立条件。
- [通过类型对齐提升搬运效率](../../simt_operator_optimization/memory_access/type_alignment_transfer.md)（`related`）：扩大 block 前必须满足类型和地址对齐，否则更大单次搬运会越界或降级。
- [非连续搬运场景减少搬运次数](reduce_non_contiguous_transfer.md)（`related`）：先减少非连续片段再放大每次 block，二者共同降低 DMA 次数和启动开销。
- [MemoryAccessMerge](../../simt_operator_optimization/memory_access/memory_access_merge.md)（`same_topic`）：《MemoryAccessMerge》处理“SIMT编程模式下让同一Warp内相邻线程访问连续GM地址以实现访存合并，提高GM带宽利用率。”。《尽量一次搬运较大的数据块》提供“【描述】搬运不同大小的数据块时，对带宽的利用率（有效带宽/理论带宽）不一样。根据实测经验，单次搬运数据长度16KB以上时，通常能较好地发挥出带宽的最佳性能。因此对于单次搬运，应考虑尽可能的搬运较大的数据块。下图展示了某款AI处理器上实测的不同搬运数据量下带宽的变化图。”，其具体合同或探针直接接入Warp 连续 GM 访问的短向量、类型对齐、步长搬运和 Gather 示例验证。
<!-- cannbot:related:end -->
