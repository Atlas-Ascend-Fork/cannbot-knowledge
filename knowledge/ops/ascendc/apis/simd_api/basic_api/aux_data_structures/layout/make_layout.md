---
type: API
title: MakeLayout
description: 将传入的Shape和Stride数据打包成Layout数据结构。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Layout/MakeLayout.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# MakeLayout

构造Layout结构体的辅助函数。通过传入shape、stride和format等信息创建Layout。函数原型提供多种重载，支持不同维度的shape和stride输入。参数包含shape各维度大小、stride各维度步长、format数据格式。返回Layout结构体。用于快速创建Tensor排布描述。

<!-- cannbot:related:start -->
## 相关

- [layout](layout1.md)（`related`）：“Layout结构体用于描述Tensor的数据排布，包含shape（各维度大小）、stride（各维度步长）和format（数据格式）等成员。”与“构造Layout结构体的辅助函数。通过传入shape、stride和format等信息创建Layout。”分别来自双方当前正文。Layout 卡定义结构体所承载的 shape、stride、format，MakeLayout 卡说明以这三类信息构造该结构体，形成数据描述与构造入口的直接关系。
<!-- cannbot:related:end -->
