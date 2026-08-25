---
type: API
title: MrgSort
description: 将已排好序的最多4条队列合并排列成1条队列，结果按照score域由大到小排序。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/sort_operations/MrgSort.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# MrgSort

将已排好序的最多4条队列合并排列成1条队列，结果按score域由大到小排序。与Sort配合使用，先对多段数据分别排序，再通过MrgSort合并。

函数原型：template <typename T> __aicore__ inline void MrgSort(LocalTensor<T>& dst, const LocalTensor<T>& src, const LocalTensor<T>& tmp, const MrgSortInfo& mrgSortInfo, const int32_t repeatTime)

参数：dst为输出操作数；src为输入操作数（最多4条已排序队列）；tmp为临时缓存；mrgSortInfo含各队列长度等排序信息；repeatTime为重复次数。约束：遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [TopK BF16 tie 索引顺序与 CPU 不一致](../../../../runbooks/precision/topk_bf16_tie_cpu.md)（`exemplifies`）：TopK BF16 tie 索引顺序与 CPU 不一致 与《MrgSort》的实质衔接是：TopK 对 tie 不保证与 CPU 相同的索引顺序；TopK/tiling 与 Sort→MrgSort→Concat/Extract 链解释内部排序，fair-oracle 卡给出集合而非逐元素索引的验证方式。
- [AscMrgsort4](../../c_api/vector_compute/asc_mrgsort4.md)（`related`）：AscMrgsort4 与《MrgSort》的实质衔接是：AscMrgsort4 的 Reg/C++ 入口、状态寄存器与结果读取必须配套，高层 MergeSort 说明同一四路归并任务如何落到该原语。
- [GetMrgSortResult](../../basic_api/memory_vector_compute/sort_and_merge/get_mrg_sort_result.md)（`related`）：《GetMrgSortResult》明确“与MrgSort接口配合使用，在队列耗尽停止后获取4个队列已处理的Region Proposal个数。”；它与《MrgSort》的“将已排好序的最多4条队列合并排列成1条队列，结果按照score域由大到小排序。”在实际调用参数、数据流或结果校验上直接衔接。
- [GetSortOffset](get_sort_offset.md)（`related`）：GetSortOffset 与《MrgSort》的实质衔接是：SortOffset 是 Sort 中间数据布局的字节偏移；SortLen、临时空间、Concat/Extract 和 Sort 调用必须采用同一 repeat 布局。
- [MrgSort](../../basic_api/memory_vector_compute/sort_and_merge/mrg_sort.md)（`same_topic`）：《MrgSort》明确“将已排序的最多4条队列合并为1条队列，结果按score域由大到小排序，通常处理Sort32预处理的数据。”；它与《MrgSort》的“将已排好序的最多4条队列合并排列成1条队列，结果按照score域由大到小排序。”在实际调用参数、数据流或结果校验上直接衔接。
- [Sort32](../../basic_api/memory_vector_compute/sort_and_merge/sort32.md)（`same_topic`）：《Sort32》处理“一次迭代内对32个数按score域降序排列，结果以score和index的结构存储在目的张量中。”。《MrgSort》提供“将已排好序的最多4条队列合并排列成1条队列，结果按照score域由大到小排序。”，其具体合同或探针直接接入Sort32 的 proposal 预处理、排序、合并和字段拆装流水。
<!-- cannbot:related:end -->
