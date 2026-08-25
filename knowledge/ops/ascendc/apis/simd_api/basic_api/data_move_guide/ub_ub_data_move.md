---
type: API
title: UB与UB数据搬运
description: Unified Buffer（UB）之间的数据搬运提供了灵活的接口支持，共有两组接口：DataCopy提供了基础的数据搬运能力，支持连续和非连续数据搬运；Copy除了支持连续和非连续数据搬运，还提供了mask操作和DataBlock间隔操作的能力，支持在接口内部和接口外部设置mask。具体接口功能如下表所示。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_move_guide/UB_UB_data_move.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# UB与UB数据搬运

Unified Buffer 间数据搬运提供两组接口。DataCopy 支持连续和高维切分（DataCopyParams：blockCount/blockLen/srcGap/dstGap）搬运。Copy 除连续和高维切分外，还支持 mask 操作（SetVectorMask）和 DataBlock 间隔操作（srcStride/dstStride 以 DataBlock 为单位），可在接口内部或外部设置 mask。UB 地址需 32B 对齐。
