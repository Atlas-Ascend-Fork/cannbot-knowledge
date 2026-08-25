---
type: API
title: Concat（排序操作）
description: 对数据进行预处理，将要排序的源操作数src一一对应的合入目标数据concat中，数据预处理完成后，可以进行Sort。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/sort_operations/Concat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Concat

对数据进行预处理，将要排序的源操作数src一一对应合入目标数据concat中，预处理完成后可进行Sort操作。

函数原型：template <typename T> __aicore__ inline void Concat(LocalTensor<T>& concat, const LocalTensor<T>& src, const LocalTensor<T>& tmp, const int32_t repeatTime)

参数：concat为目标操作数（输出）；src为源操作数（输入）；tmp为临时缓存；repeatTime为重复次数。约束：遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [TopK BF16 tie 索引顺序与 CPU 不一致](../../../../runbooks/precision/topk_bf16_tie_cpu.md)（`exemplifies`）：TopK BF16 tie 索引顺序与 CPU 不一致 与《Concat（排序操作）》的实质衔接是：TopK 对 tie 不保证与 CPU 相同的索引顺序；TopK/tiling 与 Sort→MrgSort→Concat/Extract 链解释内部排序，fair-oracle 卡给出集合而非逐元素索引的验证方式。
- [Extract（排序操作）](extract.md)（`related`）：多段排序结果先 Concat，再 Extract 有效数据。
- [GetConcatTmpSize](get_concat_tmp_size.md)（`related`）：GetConcatTmpSize 返回的大小正是 Concat 排序预处理接口的临时空间输入；查询结果和 kernel 调用是一对 host/kernel 参数合同。
- [GetSortOffset](get_sort_offset.md)（`related`）：GetSortOffset 与《Concat（排序操作）》的实质衔接是：SortOffset 是 Sort 中间数据布局的字节偏移；SortLen、临时空间、Concat/Extract 和 Sort 调用必须采用同一 repeat 布局。
- [ProposalConcat](../../basic_api/memory_vector_compute/sort_and_merge/proposal_concat.md)（`related`）：《ProposalConcat》处理“将连续元素合入Region Proposal内对应位置，每次迭代会将16个连续元素合入到16个Region Proposals的对应位置里。 Region Proposal说明： 目前仅支持两种数据类型：half、float。 每个Region Proposal占用连续8个half/float类型的元素，约定其格式：”。《Concat（排序操作）》明确提供“对数据进行预处理，将要排序的源操作数src一一对应的合入目标数据concat中，数据预处理完成后，可以进行Sort。”，其参数、调用或验证步骤直接接入ProposalConcat 与 ProposalExtract、Sort32、MrgSort 组成的 proposal 流水。
- [Sort](sort.md)（`related`）：Sort 文档要求先用 Concat 把 score/index 组织为排序输入；Concat 是 Sort 流程的显式预处理步骤。
- [Sort32](../../basic_api/memory_vector_compute/sort_and_merge/sort32.md)（`same_topic`）：《Sort32》处理“一次迭代内对32个数按score域降序排列，结果以score和index的结构存储在目的张量中。”。《Concat（排序操作）》提供“对数据进行预处理，将要排序的源操作数src一一对应的合入目标数据concat中，数据预处理完成后，可以进行Sort。”，其具体合同或探针直接接入Sort32 的 proposal 预处理、排序、合并和字段拆装流水。
<!-- cannbot:related:end -->
