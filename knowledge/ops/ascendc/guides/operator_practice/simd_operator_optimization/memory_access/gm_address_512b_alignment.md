---
type: Guide
title: GM地址尽量512B对齐
description: 【描述】由于AI处理器内部设计约束，从GM向Local Memory搬运数据时，保证GM地址512B对齐可以最有效的发挥出带宽的效率。如下图示例，展示了在512B对齐以及32B对齐情况下单核的带宽效率：搬运同等数据量，带宽差距最大的情况，32B对齐场景只能达到512B对齐场景的70%。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/memory_access/gm_address_512b_alignment.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2]
---

# GM地址尽量512B对齐

【优先级】高

【描述】由于AI处理器内部设计约束，从GM向Local Memory搬运数据时，保证GM地址512B对齐可以最有效的发挥出带宽的效率。如下图示例，展示了在512B对齐以及32B对齐情况下单核的带宽效率：搬运同等数据量，带宽差距最大的情况，32B对齐场景只能达到512B对齐场景的70%。

>- 本性能优化手段仅针对Atlas A2 训练系列产品/Atlas A2 推理系列产品生效。
>- 测试数据与处理器型号相关，且实际测试时可能会存在略微抖动，具体带宽数值并不一定和下文的测试数据严格一致。

**图1**  GM->UB方向512B对齐和32B对齐实测带宽的差异对比

**图2**  UB->GM方向512B对齐和32B对齐实测带宽的差异对比

<!-- cannbot:related:start -->
## 相关

- [尽量一次搬运较大的数据块](transfer_larger_data_blocks.md)（`related`）：在基址对齐之外，单次搬运块达到约 16KB 才能进一步提高有效带宽，补足地址与长度两个独立条件。
- [通过类型对齐提升搬运效率](../../simt_operator_optimization/memory_access/type_alignment_transfer.md)（`related`）：GM 基址 512B 对齐关注事务起点，SIMT 类型对齐关注单次访问宽度；两者共同减少非合并/低效 GM 事务。
- [避免同地址访问](avoid_same_address_access.md)（`related`）：GM地址尽量512B对齐说明【描述】由于AI处理器内部设计约束，从GM向Local Memory搬运数据时，保证GM地址512B对齐可以最有效的发挥出带宽的效率。如下图示例，展示了在512B对齐以及32B对齐情况下单核的带宽效率：搬运同等数据量，带宽差距最大的情况，32B对齐场景只能达到512B对齐场景的70%。
- [MemoryAccessMerge](../../simt_operator_optimization/memory_access/memory_access_merge.md)（`same_topic`）：《MemoryAccessMerge》处理“SIMT编程模式下让同一Warp内相邻线程访问连续GM地址以实现访存合并，提高GM带宽利用率。”。《GM地址尽量512B对齐》提供“【描述】由于AI处理器内部设计约束，从GM向Local Memory搬运数据时，保证GM地址512B对齐可以最有效的发挥出带宽的效率。如下图示例，展示了在512B对齐以及32B对齐情况下单核的带宽效率：搬运同等数据量，带宽差距最大的情况，32B对齐场景只能达到512B对齐场景的70%。”，其具体合同或探针直接接入Warp 连续 GM 访问的短向量、类型对齐、步长搬运和 Gather 示例验证。
<!-- cannbot:related:end -->
