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

- [Concat（排序操作）](concat.md)（`related`）：焦点卡说明“预处理完成后可进行Sort操作”，候选卡则要求 Sort“配合Concat（预处理）和Extract（结果提取）使用”；Concat 是排序前的实际数据整形阶段，而不是仅同属排序目录的 sibling。
- [Extract（排序操作）](extract.md)（`related`）：焦点卡把参数合同写为“sorted输入Sort的结果数据”，候选卡明确 Sort 要“配合Concat（预处理）和Extract（结果提取）使用。”；Sort 的结构化 score/index 输出正是 Extract 的直接输入。
- [GetSortLen](get_sort_len.md)（`related`）：获取Sort接口处理的数据长度。；排序函数，按照数值大小进行降序排序。支持带和不带SortConfig模板参数两种原型。不带Config时执行标准降序排序；带Config时可配置排序参数。。GetSortLen 按 repeatTime 计算 Sort 处理长度，Sort 卡给出该长度所服务的降序 score/index 执行接口与临时空间合同。
- [GetSortMaxMinTmpSize](get_sort_max_min_tmp_size.md)（`related`）：host侧Tiling接口，用于获取Sort接口所需的最大和最小临时空间大小。；提供通过sharedTmpBuffer传入临时空间或由接口框架申请两种重载。临时空间大小通过GetSortMaxMinTmpSize获取。。Sort 明确把显式 sharedTmpBuffer 的容量查询委托给 GetSortMaxMinTmpSize，二者是直接的 Host Tiling 与 Kernel 调用合同。
- [InplaceIndexFill 950 ACLNN 算子知识](../../../../operators/aclnn/nn/index/inplace_index_fill_950.md)（`related`）：“Dense 路线在 mask 前增加 `GM indices → VECIN TQue → Sort/MicroAPI Unique → mask`。”；“排序函数，按照数值大小进行降序排序。支持带和不带SortConfig模板参数两种原型。”。950 极密索引路线先排序再去重以减少共享 mask 同址写，Sort API 提供该 Dense route 的排序原语合同。
- [MrgSort](mrg_sort.md)（`related`）：将已排好序的最多4条队列合并排列成1条队列，结果按score域由大到小排序。与Sort配合使用，先对多段数据分别排序，再通过MrgSort合并。；排序函数，按照数值大小进行降序排序。支持带和不带SortConfig模板参数两种原型。不带Config时执行标准降序排序；带Config时可配置排序参数。排序后的数据排布方式因产品型号而异（950PR/950DT、A3、A2训练推理采用方式一，推理AI Core采用方式二）。模板参数T支持half/float/int16_t/uint16_t。；MrgSort 明确要求先由 Sort 产生分段已排序队列，目标给出该生产接口与结果布局边界。
<!-- cannbot:related:end -->
