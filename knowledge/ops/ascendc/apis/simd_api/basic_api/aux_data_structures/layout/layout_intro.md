---
type: API
title: Layout简介
description: Layout数据结构是描述多维张量内存布局的基础模板类，通过编译时的形状（Shape）和步长（Stride）信息，实现逻辑坐标空间到一维内存地址空间的映射，为复杂张量操作和硬件优化提供基础支持。借助模板元编程技术，该类在编译时完成计算和代码生成，从而降低运行时开销。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Layout/Layout_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---


# Layout简介

Layout是描述Tensor数据排布的结构体，包含shape（各维度大小）、stride（各维度步长）和format（数据格式）等信息。Layout用于描述Tensor在内存中的实际排布方式，支持ND、NZ等格式。通过MakeLayout构造Layout，可指定shape、stride和format。Layout支持通过GetShape获取形状、GetStride获取步长、通过operator==判断两个Layout是否相等。Layout与TensorDesc/TensorTrait配合使用，描述Tensor的完整信息。
