---
type: API
title: DataCopy
description: 支持GM与UB之间的高维切分数据搬运，支持非连续和连续的数据搬运。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopy_GMAndUB_highdim_split.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# DataCopy GM与UB高维切分搬运

支持 Global Memory 与 Unified Buffer 之间的高维切分数据搬运，数据在传输过程中保持原始格式和内容不变。头文件为 basic_api/kernel_operator_data_copy_intf.h。
通过 DataCopyParams 配置 blockCount（数据块个数）、blockLen（单个数据块长度）、srcGap（源地址偏移）、dstGap（目的地址偏移），同时支持非连续和连续的数据搬运。
支持的数据通路包括 GM 到 VECIN（UB）与 VECOUT（UB）到 GM；Atlas 推理系列产品 AI Core 还支持 CO2 到 GM。
连续搬运场景推荐使用 DataCopy GM 与 UB 连续数据搬运接口以获得更好性能。
支持 Ascend 950PR/950DT、Atlas A2、Atlas A3、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品 AI Core 与 Vector Core 以及 Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [DataCopy](data_copy_gm_and_ub_continuous.md)（`same_topic`）：当高维参数退化为连续访问时，以“连续搬运场景推荐使用 DataCopy GM 与 UB 连续数据搬运接口以获得更好性能。”作选型触发，并用“支持GM与UB之间的连续数据搬运，数据传输过程中保持原始格式和内容不变。”确认连续接口保持格式和内容不变，从而减少不必要的高维配置开销。
- [DataCopy](data_copy_gm_and_ub_slice.md)（`same_topic`）：软仿接口，支持数据的切片搬运，提取多维Tensor数据的子集进行搬运。；通过 DataCopyParams 配置 blockCount（数据块个数）、blockLen（单个数据块长度）、srcGap（源地址偏移）、dstGap（目的地址偏移），同时支持非连续和连续的数据搬运。。两端都解决 GM 与 UB 的多维非连续子集搬运；切片端以 SliceInfo 表达区间，HighDimSplit 端以块数、块长和 gap 表达相同搬运任务的另一参数化路径。
<!-- cannbot:related:end -->
