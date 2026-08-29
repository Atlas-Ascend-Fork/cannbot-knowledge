---
type: API
title: AscGetVms4Sr
description: 此接口用于获取执行asc_mrgsort4操作后的4个队列中，每个队列已经理过的Region Proposal个数。使用时，需要将asc_mrgsort4中的if_exhausted_suspension参数配置为true，该配置模式下某条队列耗尽后，MrgSort4指令停止。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_get_vms4_sr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscGetVms4Sr

此接口用于获取执行asc_mrgsort4操作后的4个队列中，每个队列已经理过的Region Proposal个数。使用时，需要将asc_mrgsort4中的if_exhausted_suspension参数配置为true，该配置模式下某条队列耗尽后，MrgSort4指令停止。
函数原型：void asc_get_vms4_sr(uint16_t sorted_num[ASC_C_API_MRGSORT_ELEMENT_LEN])
约束：需和asc_mrgsort4操作配合使用，且需asc_mrgsort4中的if_exhausted_suspension参数配置为true。；需通过同步操作确保asc_mrgsort4执行完成后再调用本接口获取结果。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscMrgsort4](asc_mrgsort4.md)（`related`）：将已经排好序的最多4条队列，合并排列成1条队列，结果按照score域由大到小排序。；此接口用于获取执行asc_mrgsort4操作后的4个队列中，每个队列已经理过的Region Proposal个数。使用时，需要将asc_mrgsort4中的if_exhausted_suspension参数配置为true，该配置模式下某条队列耗尽后，MrgSort4指令停止。后者读取前者在 exhausted-suspension 模式下的队列消费进度，形成排序与状态查询链。
<!-- cannbot:related:end -->
