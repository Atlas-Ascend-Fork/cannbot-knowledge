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

- [TopK BF16 tie 索引顺序与 CPU 不一致](../../../../runbooks/precision/topk_bf16_tie_cpu.md)（`exemplifies`）：将已排好序的最多4条队列合并排列成1条队列，结果按score域由大到小排序。与Sort配合使用，先对多段数据分别排序，再通过MrgSort合并。；TopK 高阶 API 对 tie 值的索引顺序未定义，其内部 Sort+MrgSort+Extract 的稳定顺序与 CPU `torch.topk` 实现不同，导致同一 tie 组内索引排列差异。这不是 kernel 计算错误，是 tie 顺序未定义语义的体现。若值集合已不等，则不是本现象，应另查真精度 bug。；焦点定义 MrgSort 的降序归并，runbook 给出它在完整 TopK 管线中遇到 tie 时的可复现验证与误诊边界。
- [Sort](sort.md)（`related`）：将已排好序的最多4条队列合并排列成1条队列，结果按score域由大到小排序。与Sort配合使用，先对多段数据分别排序，再通过MrgSort合并。；排序函数，按照数值大小进行降序排序。支持带和不带SortConfig模板参数两种原型。不带Config时执行标准降序排序；带Config时可配置排序参数。排序后的数据排布方式因产品型号而异（950PR/950DT、A3、A2训练推理采用方式一，推理AI Core采用方式二）。模板参数T支持half/float/int16_t/uint16_t。；MrgSort 明确要求先由 Sort 产生分段已排序队列，目标给出该生产接口与结果布局边界。
<!-- cannbot:related:end -->
