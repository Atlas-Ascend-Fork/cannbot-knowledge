---
type: API
title: 排序与合并概述
description: Region Proposal（简称RP）是目标检测算法中用于定位潜在目标区域的候选框。Region Proposal采用特定的数据结构进行存储和管理，以支持高效的排序和筛选操作。在业务场景下，为了从大量Region
  Proposals中筛选出最有可能包含目标的区域，需要根据每个RP的置信度score进行排序。
tags: [task.lookup, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/sort_and_merge_ISASI/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 概述

Region Proposal（简称RP）是目标检测算法中用于定位潜在目标区域的候选框。Region Proposal采用特定的数据结构进行存储和管理，以支持高效的排序和筛选操作。在业务场景下，为了从大量Region Proposals中筛选出最有可能包含目标的区域，需要根据每个RP的置信度score进行排序。

以Atlas A3 训练系列产品/Atlas A3 推理系列产品和Atlas A2 训练系列产品/Atlas A2 推理系列产品为例：

Region Proposal支持两种数据类型：half/float。

下图展示了n个Region Proposal的结构示意图，每组[x1， x2， y1，y2，score，label]代表一个完整的Region Proposal。其中，x1、x2、y1、y2表示候选框的坐标，score为置信度，label为目标的类别标签。

**图1**  Region Proposal结构示意图

排序组合接口用于实现（score, index）对的排序操作，其中index用于索引完整的RP数据，数据结构请参考Sort32排序示意图。其中，Sort32接口实现一次迭代内对32个（score, index）对的降序排列。MrgSort接口将多个（最多4个）已经排好序的子队列，归并成一个全局有序的队列。

<!-- cannbot:related:start -->
## 相关

- [AscMrgsort4](../../../c_api/vector_compute/asc_mrgsort4.md)（`related`）：AscMrgsort4 与《排序与合并概述》的实质衔接是：AscMrgsort4 的 Reg/C++ 入口、状态寄存器与结果读取必须配套，高层 MergeSort 说明同一四路归并任务如何落到该原语。
- [MrgSort](mrg_sort.md)（`related`）：《MrgSort》的任务是“将已排序的最多4条队列合并为1条队列，结果按score域由大到小排序，通常处理Sort32预处理的数据。”。《排序与合并概述》具体提供“Region Proposal（简称RP）是目标检测算法中用于定位潜在目标区域的候选框。Region Proposal采用特定的数据结构进行存储和管理，以支持高效的排序和筛选操作。在业务场景下，为了从大量Region Proposals中筛选出最有可能包含目标的区域，需要根据每个RP的置信度score进行排序。”，它直接用于Sort32 预排序、MrgSort 合并和 proposal 提取结果的流水。
- [ProposalConcat](proposal_concat.md)（`same_topic`）：《ProposalConcat》处理“将连续元素合入Region Proposal内对应位置，每次迭代会将16个连续元素合入到16个Region Proposals的对应位置里。 Region Proposal说明： 目前仅支持两种数据类型：half、float。 每个Region Proposal占用连续8个half/float类型的元素，约定其格式：”。《排序与合并概述》明确提供“Region Proposal（简称RP）是目标检测算法中用于定位潜在目标区域的候选框。Region Proposal采用特定的数据结构进行存储和管理，以支持高效的排序和筛选操作。在业务场景下，为了从大量Region Proposals中筛选出最有可能包含目标的区域，需要根据每个RP的置信度score进行排序。”，其参数、调用或验证步骤直接接入ProposalConcat 与 ProposalExtract、Sort32、MrgSort 组成的 proposal 流水。
- [Sort32](sort32.md)（`same_topic`）：《Sort32》处理“一次迭代内对32个数按score域降序排列，结果以score和index的结构存储在目的张量中。”。《排序与合并概述》提供“Region Proposal（简称RP）是目标检测算法中用于定位潜在目标区域的候选框。Region Proposal采用特定的数据结构进行存储和管理，以支持高效的排序和筛选操作。在业务场景下，为了从大量Region Proposals中筛选出最有可能包含目标的区域，需要根据每个RP的置信度score进行排序。”，其具体合同或探针直接接入Sort32 的 proposal 预处理、排序、合并和字段拆装流水。
<!-- cannbot:related:end -->
