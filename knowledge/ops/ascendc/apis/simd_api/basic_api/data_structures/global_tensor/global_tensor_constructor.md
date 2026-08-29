---
type: API
title: GlobalTensor构造函数
description: GlobalTensor构造函数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/GlobalTensor_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GlobalTensor构造函数

GlobalTensor 默认构造函数，创建空的 GlobalTensor 对象，后续通过 SetGlobalBuffer 设置 GM 地址和大小。模板参数 T 为数据类型。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [SetGlobalBuffer](set_global_buffer.md)（`related`）：GlobalTensor 默认构造函数，创建空的 GlobalTensor 对象，后续通过 SetGlobalBuffer 设置 GM 地址和大小。模板参数 T 为数据类型。支持 950/a2/a3。；传入 GM 全局数据地址和大小，初始化 GlobalTensor。参数：buffer 为 GlobalTensor 源操作数（GM 地址），bufferSize 为元素个数。支持 950/a2/a3。。构造函数只产生空对象并明确指定后接 SetGlobalBuffer，目标接口负责绑定 GM 地址和元素数，二者组成 GlobalTensor 从空对象到可访问全局内存视图的初始化顺序。
<!-- cannbot:related:end -->
