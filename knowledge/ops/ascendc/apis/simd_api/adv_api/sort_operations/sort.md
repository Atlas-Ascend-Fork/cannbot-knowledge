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
