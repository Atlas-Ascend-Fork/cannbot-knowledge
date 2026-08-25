---
type: API
title: 构造和析构函数
description: 创建与释放TensorDesc对象。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorDesc/constructor_and_destructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---


# TensorDesc构造与析构函数

TensorDesc提供默认构造函数（创建空描述符）、通过shape和data type构造、拷贝构造等。析构函数释放相关资源。构造参数可包含shape信息、数据类型、layout等。构造的TensorDesc用于描述Tensor的元信息。

<!-- cannbot:related:start -->
## 相关

- [GetDim](get_dim.md)（`related`）：构造 TensorDesc 写入 shape 后，GetDim 用于读取其维数，形成创建后校验元信息的最短链路。
- [SetShapeAddr](set_shape_addr.md)（`related`）：默认构造得到空描述符时，SetShapeAddr 可补入 shape 地址，是另一种实际初始化路径。
- [GetDataPtr](get_data_ptr.md)（`same_topic`）：焦点处理TensorDesc 数据地址读取和 GlobalTensor 包装；构造和析构函数正文说明“创建与释放TensorDesc对象”。候选说明该裸地址如何由 TensorDesc 取得并封装成可访问的 GlobalTensor。
<!-- cannbot:related:end -->
