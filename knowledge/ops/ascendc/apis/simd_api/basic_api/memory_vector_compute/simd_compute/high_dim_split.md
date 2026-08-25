---
type: API
title: 高维切分（SIMD计算）
description: 说明 SIMD 高维切分 API 如何通过 repeatTime、stride 和 mask 控制迭代、地址间隔与掩码。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/SIMD_compute/high_dim_split.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 高维切分（SIMD计算）

本接口属于 UB 矢量计算 SIMD 计算接口。

高维切分API，支持repeatTime、stride和mask参数，能控制指令的迭代执行、操作数的地址间隔和迭代内的掩码，功能更加灵活。 以Exp接口为例，接口调用形式如下： ## 迭代控制 Vector计算单元每个迭代会从UB中取出8个DataBlock（每个DataBlock数据块内部地址连续，长度为32Byte）进行计算，并写入对

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [高维切分API](../../../../../guides/programming_guide/library_api/basic_api/interface_classification/high_dim_split_api.md)（`explains`）：The high-dimension split guide explains how GetDim/SetDim/GetShape/UpdateShape are composed to partition a high-dimensional tensor safely.
- [Copy](../data_move/copy_ub_to_ub_mask_highdim_split.md)（`same_topic`）：Copy 与《高维切分（SIMD计算）》的实质衔接是：该 Copy 是 UB 高维/掩码搬运；SetMaskNorm/Count/VectorMask、ResetMask、UB 搬运指南和 AscCopy 共同决定 mask 模式、stride 与恢复步骤。
- [DataCopy](../data_move/data_copy_gm_and_ub_highdim_split.md)（`same_topic`）：DataCopy 与《高维切分（SIMD计算）》的实质衔接是：该 DataCopy 用 DataCopyParams 做 GM/UB 高维切分；slice/continuous 对照、高维 API 分类和 blockLen 窄化故障共同说明何时选用及参数类型边界。
<!-- cannbot:related:end -->
