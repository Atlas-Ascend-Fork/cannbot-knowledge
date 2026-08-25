---
type: API
title: GetMrgSortResult
description: 与MrgSort接口配合使用，在队列耗尽停止后获取4个队列已处理的Region Proposal个数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/sort_and_merge_ISASI/GetMrgSortResult.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetMrgSortResult

与MrgSort接口配合使用，在队列耗尽停止后获取4个队列已处理的Region Proposal个数。

将已经排好序的最多4条队列，合并排列成1条队列，结果按照score域由大到小排序。 MrgSort接口通常处理经过Sort32接口预处理的数据，队列结构参考Sort32功能说明。

本接口组包含 MrgSort, MrgSort4指令, MrgSort指令, MrgSort4指令。

本接口属于 UB 矢量计算排序与合并接口。

约束：不支持源操作数和目的操作数地址重叠。；dst的起始地址需要32字节对齐，src中LocalTensor的起始地址需要8字节对齐。；如果存在score[i]==score[j]并且i>j，将优先选取score[j]排在前面。；每次迭代内的数据会进行排序，不同迭代间的数据不会进行排序。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [AscMrgsort4](../../../c_api/vector_compute/asc_mrgsort4.md)（`related`）：AscMrgsort4 与《GetMrgSortResult》的实质衔接是：AscMrgsort4 的 Reg/C++ 入口、状态寄存器与结果读取必须配套，高层 MergeSort 说明同一四路归并任务如何落到该原语。
- [MrgSort](../../../adv_api/sort_operations/mrg_sort.md)（`related`）：《GetMrgSortResult》明确“与MrgSort接口配合使用，在队列耗尽停止后获取4个队列已处理的Region Proposal个数。”；它与《MrgSort》的“将已排好序的最多4条队列合并排列成1条队列，结果按照score域由大到小排序。”在实际调用参数、数据流或结果校验上直接衔接。
- [MrgSort](mrg_sort.md)（`related`）：《MrgSort》的任务是“将已排序的最多4条队列合并为1条队列，结果按score域由大到小排序，通常处理Sort32预处理的数据。”。《GetMrgSortResult》具体提供“与MrgSort接口配合使用，在队列耗尽停止后获取4个队列已处理的Region Proposal个数。”，它直接用于Sort32 预排序、MrgSort 合并和 proposal 提取结果的流水。
- [MrgSort4（排序与合并）](mrg_sort4.md)（`related`）：MrgSort4 在某个输入队列耗尽时停止；GetMrgSortResult 用于读取四个队列已消费的 Region Proposal 数，以便推进剩余合并。
- [ProposalConcat](proposal_concat.md)（`related`）：《ProposalConcat》处理“将连续元素合入Region Proposal内对应位置，每次迭代会将16个连续元素合入到16个Region Proposals的对应位置里。 Region Proposal说明： 目前仅支持两种数据类型：half、float。 每个Region Proposal占用连续8个half/float类型的元素，约定其格式：”。《GetMrgSortResult》明确提供“与MrgSort接口配合使用，在队列耗尽停止后获取4个队列已处理的Region Proposal个数。”，其参数、调用或验证步骤直接接入ProposalConcat 与 ProposalExtract、Sort32、MrgSort 组成的 proposal 流水。
- [Sort32](sort32.md)（`same_topic`）：《Sort32》处理“一次迭代内对32个数按score域降序排列，结果以score和index的结构存储在目的张量中。”。《GetMrgSortResult》提供“与MrgSort接口配合使用，在队列耗尽停止后获取4个队列已处理的Region Proposal个数。”，其具体合同或探针直接接入Sort32 的 proposal 预处理、排序、合并和字段拆装流水。
<!-- cannbot:related:end -->
