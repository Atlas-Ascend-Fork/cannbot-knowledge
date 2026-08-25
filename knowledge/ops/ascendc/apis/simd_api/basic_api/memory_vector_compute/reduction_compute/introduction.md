---
type: API
title: 归约计算概述
description: 概述 Tensor 归约计算及 ReduceSum、ReduceMax、ReduceMin、ReducePairElem 等接口能力。
tags: [task.lookup, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/reduction_compute/Introduction.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Reduction计算简介

Reduction 计算接口对 tensor 数据进行规约运算，将多维数据降维。支持 ReduceSum（求和）、ReduceMax（最大值）、ReduceMin（最小值）、ReducePairElem 等模式。通过 repeatParams 配置多轮规约，支持高维切分。
