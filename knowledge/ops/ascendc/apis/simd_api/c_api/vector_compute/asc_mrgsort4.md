---
type: API
title: AscMrgsort4
description: 将最多 4 条已排序队列合并为 1 条队列，并按 Region Proposal 的 score 域从大到小排序。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_mrgsort4.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# AscMrgsort4

将已经排好序的最多4条队列，合并排列成1条队列，结果按照score域由大到小排序。 asc_mrgsort4处理的数据一般是经过asc_bitsort指令处理后的数据，也就是asc_bitsort指令的输出，队列的结构Region Proposal如下所示：
函数原型：void asc_mrgsort4(__ubuf__ half* dst, __ubuf__ half* src[ASC_C_API_MRGSORT_ELEMENT_LEN], uint8_t repeat, uint16_t element_length_0, uint16_t element_length_1, uint16_t element_length_2, uint16_t element_length_3, bool if_exhausted_suspension, uint8_t valid_bit)
约束：当repeat=1时，表示进行一次迭代，可自由设置element_length_..., if_exhausted_suspension, valid_bit参数。；当repeat>1时，表示进行多次迭代，必须满足以下条件：包含四条源队列，四个源队列的长度一致且在内存中连续存储，valid_bit的值为15，if_exhausted_suspension的值为false。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [GetMrgSortResult](../../basic_api/memory_vector_compute/sort_and_merge/get_mrg_sort_result.md)（`related`）：AscMrgsort4 与《GetMrgSortResult》的实质衔接是：AscMrgsort4 的 Reg/C++ 入口、状态寄存器与结果读取必须配套，高层 MergeSort 说明同一四路归并任务如何落到该原语。
- [MrgSort](../../adv_api/sort_operations/mrg_sort.md)（`related`）：AscMrgsort4 与《MrgSort》的实质衔接是：AscMrgsort4 的 Reg/C++ 入口、状态寄存器与结果读取必须配套，高层 MergeSort 说明同一四路归并任务如何落到该原语。
- [MrgSort4（排序与合并）](../../basic_api/memory_vector_compute/sort_and_merge/mrg_sort4.md)（`related`）：AscMrgsort4 与《MrgSort4（排序与合并）》的实质衔接是：AscMrgsort4 的 Reg/C++ 入口、状态寄存器与结果读取必须配套，高层 MergeSort 说明同一四路归并任务如何落到该原语。
- [ProposalConcat](../../basic_api/memory_vector_compute/sort_and_merge/proposal_concat.md)（`related`）：《ProposalConcat》处理“将连续元素合入Region Proposal内对应位置，每次迭代会将16个连续元素合入到16个Region Proposals的对应位置里。 Region Proposal说明： 目前仅支持两种数据类型：half、float。 每个Region Proposal占用连续8个half/float类型的元素，约定其格式：”。《AscMrgsort4》明确提供“将最多 4 条已排序队列合并为 1 条队列，并按 Region Proposal 的 score 域从大到小排序。”，其参数、调用或验证步骤直接接入ProposalConcat 与 ProposalExtract、Sort32、MrgSort 组成的 proposal 流水。
- [排序与合并概述](../../basic_api/memory_vector_compute/sort_and_merge/overview.md)（`related`）：AscMrgsort4 与《排序与合并概述》的实质衔接是：AscMrgsort4 的 Reg/C++ 入口、状态寄存器与结果读取必须配套，高层 MergeSort 说明同一四路归并任务如何落到该原语。
- [AscGetVms4Sr](asc_get_vms4_sr.md)（`same_topic`）：《AscMrgsort4》给出“将最多 4 条已排序队列合并为 1 条队列，并按 Region Proposal 的 score 域从大到小排序。”；该约束/探针可直接复现、解释或前置验证《AscGetVms4Sr》中的“此接口用于获取执行asc_mrgsort4操作后的4个队列中，每个队列已经理过的Region Proposal个数。使用时，需要将asc_mrgsort4中的if_exhausted_suspension参数配置为true，该配置模式下某条队列耗尽后，MrgSort4指令停止。”。
- [MrgSort](../../basic_api/memory_vector_compute/sort_and_merge/mrg_sort.md)（`same_topic`）：《MrgSort》的任务是“将已排序的最多4条队列合并为1条队列，结果按score域由大到小排序，通常处理Sort32预处理的数据。”。《AscMrgsort4》具体提供“将最多 4 条已排序队列合并为 1 条队列，并按 Region Proposal 的 score 域从大到小排序。”，它直接用于Sort32 预排序、MrgSort 合并和 proposal 提取结果的流水。
<!-- cannbot:related:end -->
