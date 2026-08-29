---
type: API
title: TensorDesc简介
description: TensorDesc用于储存ListTensorDesc.GetDesc\(\)中根据index获取对应的Tensor描述信息。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorDesc/TensorDesc_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# TensorDesc简介

TensorDesc是Tensor描述符，用于描述Tensor的元信息，包括shape（形状）、data type（数据类型）、layout（排布）和地址等。TensorDesc提供GetShape、GetDim、GetDataPtr等接口查询Tensor属性，也提供SetShapeAddr等接口修改Tensor信息。常与ListTensorDesc配合管理多个Tensor。
