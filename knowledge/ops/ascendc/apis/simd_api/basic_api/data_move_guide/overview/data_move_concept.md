---
type: API
title: 数据搬运概念（概述）
description: 数据搬运类接口提供了全面的数据搬运功能，覆盖从最基础的连续搬运到复杂的随路转换和量化激活。按照功能复杂度递增，搬运能力可以分为以下几个类别：基础数据搬运、高维切分搬运、切片搬运、随路格式转换搬运、随路量化激活搬运、非对齐搬运、UB内部搬运（Copy）、矩阵分形搬运和多维数据搬运NDDMA。每一类在后续章节中都有对应的详细接口说明。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_move_guide/overview/data_move_concept.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 数据搬运概念（概述）

数据搬运按功能复杂度递增分为：基础连续搬运（DataCopy，count 参数指定元素数）、高维切分搬运（DataCopyParams：blockLen/blockCount/srcStride/dstStride/repeat，DataBlock 32B 为单位）、切片搬运（SliceInfo 多维子区域提取）、随路格式转换（ND2NZ/NZ2ND/DN2NZ，搬运同时完成格式转换）、随路量化激活搬运（L0C→GM 的 quant/ReLU）、非对齐搬运（DataCopyPad，自定义 Padding）、UB 内部搬运（Copy，支持 mask）、矩阵分形搬运（LoadData，512B 分形）和多维数据搬运（NDDMA，自由配置维度和 Stride）。
