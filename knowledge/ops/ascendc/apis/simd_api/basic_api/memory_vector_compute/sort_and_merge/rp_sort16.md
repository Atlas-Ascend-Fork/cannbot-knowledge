---
type: API
title: RpSort16（排序与合并）
description: 根据Region Proposals中的score域对其进行排序（score大的排前面），每次排16个Region Proposals。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/sort_and_merge_ISASI/RpSort16.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# RpSort16（排序与合并）

根据Region Proposals中的score域对其进行排序（score大的排前面），每次排16个Region Proposals。

根据Region Proposals中的score域对其进行排序（score大的排前面），每次排16个Region Proposals。

本接口属于 UB 矢量计算排序与合并接口。

支持的数据类型为 half。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：用户需保证src和dst中存储的Region Proposal数目大于实际所需数据，否则会存在tensor越界错误。；当存在proposal[i]与proposal[j]的score值相同时，如果i>j，则proposal[j]将首先被选出来，排在前面。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Atlas 推理系列产品AI Core, Atlas 训练系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [MrgSort4（排序与合并）](mrg_sort4.md)（`related`）：RpSort16 先把每组 16 个 proposal 按 score 排序，MrgSort4 再把最多四条已排序队列合并，是候选框排序流水的直接下游。
- [ProposalConcat](proposal_concat.md)（`related`）：RpSort16 假定每个 Region Proposal 采用 8 元素结构；ProposalConcat 可把分离字段组装成该结构，作为排序前的数据准备。
- [ProposalExtract](proposal_extract.md)（`related`）：排序后若需要连续读取 score/index 等单字段，ProposalExtract 可从 16 个 RP 中抽取并重排，是 RpSort16 结果的常见后处理。
- [Sort32](sort32.md)（`related`）：Sort32 面向 score+index 的 32 元素排序，而 RpSort16 面向 8 字段 Region Proposal；二者的输入布局与后续归并链不同，可用于选型。
<!-- cannbot:related:end -->
