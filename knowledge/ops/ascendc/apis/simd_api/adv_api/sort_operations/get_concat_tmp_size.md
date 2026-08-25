---
type: API
title: GetConcatTmpSize
description: 获取Concat接口所需的临时空间大小，单位为字节。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/sort_operations/GetConcatTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetConcatTmpSize

获取Concat接口所需的临时空间大小。

函数原型：void GetConcatTmpSize(const int32_t repeatTime, uint32_t& maxValue)

参数：repeatTime为重复次数；maxValue输出所需临时空间大小。约束：无。

<!-- cannbot:related:start -->
## 相关

- [Concat（排序操作）](concat.md)（`related`）：GetConcatTmpSize 返回的大小正是 Concat 排序预处理接口的临时空间输入；查询结果和 kernel 调用是一对 host/kernel 参数合同。
- [ProposalConcat](../../basic_api/memory_vector_compute/sort_and_merge/proposal_concat.md)（`related`）：《ProposalConcat》处理“将连续元素合入Region Proposal内对应位置，每次迭代会将16个连续元素合入到16个Region Proposals的对应位置里。 Region Proposal说明： 目前仅支持两种数据类型：half、float。 每个Region Proposal占用连续8个half/float类型的元素，约定其格式：”。《GetConcatTmpSize》明确提供“获取Concat接口所需的临时空间大小，单位为字节。”，其参数、调用或验证步骤直接接入ProposalConcat 与 ProposalExtract、Sort32、MrgSort 组成的 proposal 流水。
<!-- cannbot:related:end -->
