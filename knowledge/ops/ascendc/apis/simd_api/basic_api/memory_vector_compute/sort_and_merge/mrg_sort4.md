---
type: API
title: MrgSort4（排序与合并）
description: 将已经排好序的最多4条Region Proposals队列，排列并合并成1条队列，结果按照score域由大到小排序。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/sort_and_merge_ISASI/MrgSort4.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# MrgSort4（排序与合并）

将已经排好序的最多4条Region Proposals队列，排列并合并成1条队列，结果按照score域由大到小排序。

将已经排好序的最多4条Region Proposals队列，排列并合并成1条队列，结果按照score域由大到小排序。

本接口属于 UB 矢量计算排序与合并接口。

支持的数据类型为 half。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：当存在proposal[i]与proposal[j]的score值相同时，如果i>j，则proposal[j]将首先被选出来，排在前面。；操作数地址对齐要求请参见通用地址对齐约束。；不支持源操作数与目的操作数之间存在地址重叠。

支持的硬件型号：Atlas 推理系列产品AI Core, Atlas 训练系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [AscMrgsort4](../../../c_api/vector_compute/asc_mrgsort4.md)（`related`）：AscMrgsort4 与《MrgSort4（排序与合并）》的实质衔接是：AscMrgsort4 的 Reg/C++ 入口、状态寄存器与结果读取必须配套，高层 MergeSort 说明同一四路归并任务如何落到该原语。
- [GetMrgSortResult](get_mrg_sort_result.md)（`related`）：MrgSort4 在某个输入队列耗尽时停止；GetMrgSortResult 用于读取四个队列已消费的 Region Proposal 数，以便推进剩余合并。
- [RpSort16（排序与合并）](rp_sort16.md)（`related`）：RpSort16 先把每组 16 个 proposal 按 score 排序，MrgSort4 再把最多四条已排序队列合并，是候选框排序流水的直接下游。
- [ProposalConcat](proposal_concat.md)（`same_topic`）：《ProposalConcat》处理“将连续元素合入Region Proposal内对应位置，每次迭代会将16个连续元素合入到16个Region Proposals的对应位置里。 Region Proposal说明： 目前仅支持两种数据类型：half、float。 每个Region Proposal占用连续8个half/float类型的元素，约定其格式：”。《MrgSort4（排序与合并）》明确提供“将已经排好序的最多4条Region Proposals队列，排列并合并成1条队列，结果按照score域由大到小排序。”，其参数、调用或验证步骤直接接入ProposalConcat 与 ProposalExtract、Sort32、MrgSort 组成的 proposal 流水。
<!-- cannbot:related:end -->
