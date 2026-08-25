---
type: API
title: AscMrgsort4
description: 将最多 4 条已排序队列合并为 1 条队列，并按 Region Proposal 的 score 域从大到小排序。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_mrgsort4.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# AscMrgsort4

将已经排好序的最多4条队列，合并排列成1条队列，结果按照score域由大到小排序。 asc_mrgsort4处理的数据一般是经过asc_bitsort指令处理后的数据，也就是asc_bitsort指令的输出，队列的结构Region Proposal如下所示：
函数原型：void asc_mrgsort4(__ubuf__ half* dst, __ubuf__ half* src[ASC_C_API_MRGSORT_ELEMENT_LEN], uint8_t repeat, uint16_t element_length_0, uint16_t element_length_1, uint16_t element_length_2, uint16_t element_length_3, bool if_exhausted_suspension, uint8_t valid_bit)
约束：当repeat=1时，表示进行一次迭代，可自由设置element_length_..., if_exhausted_suspension, valid_bit参数。；当repeat>1时，表示进行多次迭代，必须满足以下条件：包含四条源队列，四个源队列的长度一致且在内存中连续存储，valid_bit的值为15，if_exhausted_suspension的值为false。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等
