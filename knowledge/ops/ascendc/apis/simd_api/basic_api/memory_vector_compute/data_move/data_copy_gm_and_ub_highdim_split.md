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

- [DataCopyExtParams blockLen 窄化编译失败](../../../../../runbooks/compilation/datacopyextparams_block_len_requires_uint32.md)（`exemplifies`）：DataCopy 与《DataCopyExtParams blockLen 窄化编译失败》的实质衔接是：该 DataCopy 用 DataCopyParams 做 GM/UB 高维切分；slice/continuous 对照、高维 API 分类和 blockLen 窄化故障共同说明何时选用及参数类型边界。
- [高维切分API](../../../../../guides/programming_guide/library_api/basic_api/interface_classification/high_dim_split_api.md)（`explains`）：DataCopy 与《高维切分API》的实质衔接是：该 DataCopy 用 DataCopyParams 做 GM/UB 高维切分；slice/continuous 对照、高维 API 分类和 blockLen 窄化故障共同说明何时选用及参数类型边界。
- [DataCopy](data_copy_ub_to_ub_highdim_split.md)（`related`）：GM-UB 高维切分使用相同 blockCount、blockLen 与 stride 模型，但跨存储层并受 MTE 路径约束。
- [数据搬运](data_move.md)（`related`）：DataCopy 与《数据搬运》的实质衔接是：该 DataCopy 用 DataCopyParams 做 GM/UB 高维切分；slice/continuous 对照、高维 API 分类和 blockLen 窄化故障共同说明何时选用及参数类型边界。
- [DataCopy](data_copy_gm_and_ub_continuous.md)（`same_topic`）：DataCopy 与《DataCopy》的实质衔接是：该 DataCopy 用 DataCopyParams 做 GM/UB 高维切分；slice/continuous 对照、高维 API 分类和 blockLen 窄化故障共同说明何时选用及参数类型边界。
- [DataCopy](data_copy_gm_and_ub_slice.md)（`same_topic`）：《DataCopy》说明软仿接口，支持数据的切片搬运，提取多维Tensor数据的子集进行搬运。；《DataCopy》说明支持GM与UB之间的高维切分数据搬运，支持非连续和连续的数据搬运。。二者在切片DataCopy是高维分块搬运的具体重载，连续搬运和数据搬运总览用于界定它的适用边界上存在可执行的直接衔接。
- [高维切分（SIMD计算）](../simd_compute/high_dim_split.md)（`same_topic`）：DataCopy 与《高维切分（SIMD计算）》的实质衔接是：该 DataCopy 用 DataCopyParams 做 GM/UB 高维切分；slice/continuous 对照、高维 API 分类和 blockLen 窄化故障共同说明何时选用及参数类型边界。
<!-- cannbot:related:end -->
