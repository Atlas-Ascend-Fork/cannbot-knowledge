---
type: API
title: Extract（排序操作）
description: 处理Sort的结果数据，输出排序后的value和index。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/sort_operations/Extract.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Extract

处理Sort的结果数据，输出排序后的value和index。

函数原型：template <typename T> __aicore__ inline void Extract(const LocalTensor<T>& dstValue, const LocalTensor<uint32_t>& dstIndex, const LocalTensor<T>& sorted, const int32_t repeatTime)

参数：dstValue输出排序后的值；dstIndex输出排序后的索引；sorted输入Sort的结果数据；repeatTime为重复次数。约束：遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [TopK BF16 tie 索引顺序与 CPU 不一致](../../../../runbooks/precision/topk_bf16_tie_cpu.md)（`exemplifies`）：TopK BF16 tie 索引顺序与 CPU 不一致 与《Extract（排序操作）》的实质衔接是：TopK 对 tie 不保证与 CPU 相同的索引顺序；TopK/tiling 与 Sort→MrgSort→Concat/Extract 链解释内部排序，fair-oracle 卡给出集合而非逐元素索引的验证方式。
- [noTrans extract 与 NDExtLayoutPtn 方向不匹配](../../../../runbooks/precision/notrans_extract_ndextlayoutptn.md)（`exemplifies`）：该卡说明 NoTrans Extract 需要正确 ND ExtLayoutPtn，否则输出布局错。
- [Concat（排序操作）](concat.md)（`related`）：多段排序结果先 Concat，再 Extract 有效数据。
- [GetSortLen](get_sort_len.md)（`related`）：有效排序长度决定 Extract 范围。
- [GetSortOffset](get_sort_offset.md)（`related`）：GetSortOffset 与《Extract（排序操作）》的实质衔接是：SortOffset 是 Sort 中间数据布局的字节偏移；SortLen、临时空间、Concat/Extract 和 Sort 调用必须采用同一 repeat 布局。
- [Sort](sort.md)（`related`）：Sort 输出按 score/index 组合结构排布，Extract 是文档指定的结果拆取步骤，二者构成排序后的直接处理链。
<!-- cannbot:related:end -->
