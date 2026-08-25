---
type: API
title: Sort
description: 排序函数，按照数值大小进行降序排序，排序结果以score和index结构存储。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/sort_operations/Sort.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Sort

排序函数，按照数值大小进行降序排序。支持带和不带SortConfig模板参数两种原型。不带Config时执行标准降序排序；带Config时可配置排序参数。排序后的数据排布方式因产品型号而异（950PR/950DT、A3、A2训练推理采用方式一，推理AI Core采用方式二）。模板参数T支持half/float/int16_t/uint16_t。

提供通过sharedTmpBuffer传入临时空间或由接口框架申请两种重载。临时空间大小通过GetSortMaxMinTmpSize获取。接口参数：dstTensor输出排序结果；srcTensor输入数据；sharedTmpBuffer临时缓存；repeatTime重复次数。TPosition支持VECIN/VECCALC/VECOUT。

约束：遵循通用地址对齐约束。配合Concat（预处理）和Extract（结果提取）使用。

<!-- cannbot:related:start -->
## 相关

- [TopK BF16 tie 索引顺序与 CPU 不一致](../../../../runbooks/precision/topk_bf16_tie_cpu.md)（`exemplifies`）：TopK BF16 tie 索引顺序与 CPU 不一致 与《Sort》的实质衔接是：TopK 对 tie 不保证与 CPU 相同的索引顺序；TopK/tiling 与 Sort→MrgSort→Concat/Extract 链解释内部排序，fair-oracle 卡给出集合而非逐元素索引的验证方式。
- [Concat（排序操作）](concat.md)（`related`）：Sort 文档要求先用 Concat 把 score/index 组织为排序输入；Concat 是 Sort 流程的显式预处理步骤。
- [Extract（排序操作）](extract.md)（`related`）：Sort 输出按 score/index 组合结构排布，Extract 是文档指定的结果拆取步骤，二者构成排序后的直接处理链。
- [GetSortMaxMinTmpSize](get_sort_max_min_tmp_size.md)（`related`）：Sort 支持框架申请或外部 sharedTmpBuffer 两种重载，外部缓存的合法大小由 GetSortMaxMinTmpSize 明确给出。
- [GetSortOffset](get_sort_offset.md)（`related`）：GetSortOffset 与《Sort》的实质衔接是：SortOffset 是 Sort 中间数据布局的字节偏移；SortLen、临时空间、Concat/Extract 和 Sort 调用必须采用同一 repeat 布局。
<!-- cannbot:related:end -->
