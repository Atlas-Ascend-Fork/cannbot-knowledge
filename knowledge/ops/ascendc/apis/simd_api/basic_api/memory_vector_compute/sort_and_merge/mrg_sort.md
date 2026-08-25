---
type: API
title: MrgSort
description: 将已排序的最多4条队列合并为1条队列，结果按score域由大到小排序，通常处理Sort32预处理的数据。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/sort_and_merge_ISASI/MrgSort.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# MrgSort

将已排序的最多4条队列合并为1条队列，结果按score域由大到小排序，通常处理Sort32预处理的数据。

Sort32接口实现一次迭代内对32个数的降序排列操作。 如下图所示，src0和src1分别表示待排序的数据score和对应RP的索引index，排序完成后以（score, index）的结构存储在dst中。 src1固定为uint32_t类型，无论src0是float还是half类型，dst中的（score, index）结构总是占据8B空间。其中： - 当src0为float类型时，dst中的index存储在高4B，score存储在低4B； - 当src0为half类型时，dst中index存储在高4B，score存储在低2B，中间的2B保留。 图1 Sort32排序示意图

本接口组包含 Sort32功能说明, Reg矢量计算。

本接口属于 UB 矢量计算排序与合并接口。

约束：地址对齐约束参考通用地址对齐约束。；当参数repeatTime取值为0时，该接口的行为如下：；针对如下型号，当参数repeatTime取值为0时，不会执行计算操作，不会对目的操作数进行写入，该接口将被视为NOP（空操作）。；Atlas A3 训练系列产品/Atlas A3 推理系列产品

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [TopK BF16 tie 索引顺序与 CPU 不一致](../../../../../runbooks/precision/topk_bf16_tie_cpu.md)（`exemplifies`）：TopK BF16 tie 索引顺序与 CPU 不一致 与《MrgSort》的实质衔接是：TopK 对 tie 不保证与 CPU 相同的索引顺序；TopK/tiling 与 Sort→MrgSort→Concat/Extract 链解释内部排序，fair-oracle 卡给出集合而非逐元素索引的验证方式。
- [GetMrgSortResult](get_mrg_sort_result.md)（`related`）：《MrgSort》的任务是“将已排序的最多4条队列合并为1条队列，结果按score域由大到小排序，通常处理Sort32预处理的数据。”。《GetMrgSortResult》具体提供“与MrgSort接口配合使用，在队列耗尽停止后获取4个队列已处理的Region Proposal个数。”，它直接用于Sort32 预排序、MrgSort 合并和 proposal 提取结果的流水。
- [ProposalConcat](proposal_concat.md)（`related`）：《ProposalConcat》处理“将连续元素合入Region Proposal内对应位置，每次迭代会将16个连续元素合入到16个Region Proposals的对应位置里。 Region Proposal说明： 目前仅支持两种数据类型：half、float。 每个Region Proposal占用连续8个half/float类型的元素，约定其格式：”。《MrgSort》明确提供“将已排序的最多4条队列合并为1条队列，结果按score域由大到小排序，通常处理Sort32预处理的数据。”，其参数、调用或验证步骤直接接入ProposalConcat 与 ProposalExtract、Sort32、MrgSort 组成的 proposal 流水。
- [ProposalExtract](proposal_extract.md)（`related`）：《MrgSort》的任务是“将已排序的最多4条队列合并为1条队列，结果按score域由大到小排序，通常处理Sort32预处理的数据。”。《ProposalExtract》具体提供“与ProposalConcat功能相反，从Region Proposals内将相应位置的单个元素抽取后重排，每次迭代处理16个Region Proposals，抽取16个元素后连续排列。”，它直接用于Sort32 预排序、MrgSort 合并和 proposal 提取结果的流水。
- [Sort32](sort32.md)（`related`）：《MrgSort》的任务是“将已排序的最多4条队列合并为1条队列，结果按score域由大到小排序，通常处理Sort32预处理的数据。”。《Sort32》具体提供“一次迭代内对32个数按score域降序排列，结果以score和index的结构存储在目的张量中。”，它直接用于Sort32 预排序、MrgSort 合并和 proposal 提取结果的流水。
- [排序与合并概述](overview.md)（`related`）：《MrgSort》的任务是“将已排序的最多4条队列合并为1条队列，结果按score域由大到小排序，通常处理Sort32预处理的数据。”。《排序与合并概述》具体提供“Region Proposal（简称RP）是目标检测算法中用于定位潜在目标区域的候选框。Region Proposal采用特定的数据结构进行存储和管理，以支持高效的排序和筛选操作。在业务场景下，为了从大量Region Proposals中筛选出最有可能包含目标的区域，需要根据每个RP的置信度score进行排序。”，它直接用于Sort32 预排序、MrgSort 合并和 proposal 提取结果的流水。
- [AscMrgsort4](../../../c_api/vector_compute/asc_mrgsort4.md)（`same_topic`）：《MrgSort》的任务是“将已排序的最多4条队列合并为1条队列，结果按score域由大到小排序，通常处理Sort32预处理的数据。”。《AscMrgsort4》具体提供“将最多 4 条已排序队列合并为 1 条队列，并按 Region Proposal 的 score 域从大到小排序。”，它直接用于Sort32 预排序、MrgSort 合并和 proposal 提取结果的流水。
- [MrgSort](../../../adv_api/sort_operations/mrg_sort.md)（`same_topic`）：《MrgSort》明确“将已排序的最多4条队列合并为1条队列，结果按score域由大到小排序，通常处理Sort32预处理的数据。”；它与《MrgSort》的“将已排好序的最多4条队列合并排列成1条队列，结果按照score域由大到小排序。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
