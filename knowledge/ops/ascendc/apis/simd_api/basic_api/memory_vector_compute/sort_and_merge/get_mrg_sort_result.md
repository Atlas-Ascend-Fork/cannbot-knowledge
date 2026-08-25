---
type: API
title: GetMrgSortResult
description: 与MrgSort接口配合使用，在队列耗尽停止后获取4个队列已处理的Region Proposal个数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/sort_and_merge_ISASI/GetMrgSortResult.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetMrgSortResult

与MrgSort接口配合使用，在队列耗尽停止后获取4个队列已处理的Region Proposal个数。

将已经排好序的最多4条队列，合并排列成1条队列，结果按照score域由大到小排序。 MrgSort接口通常处理经过Sort32接口预处理的数据，队列结构参考Sort32功能说明。

本接口组包含 MrgSort, MrgSort4指令, MrgSort指令, MrgSort4指令。

本接口属于 UB 矢量计算排序与合并接口。

约束：不支持源操作数和目的操作数地址重叠。；dst的起始地址需要32字节对齐，src中LocalTensor的起始地址需要8字节对齐。；如果存在score[i]==score[j]并且i>j，将优先选取score[j]排在前面。；每次迭代内的数据会进行排序，不同迭代间的数据不会进行排序。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
