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
