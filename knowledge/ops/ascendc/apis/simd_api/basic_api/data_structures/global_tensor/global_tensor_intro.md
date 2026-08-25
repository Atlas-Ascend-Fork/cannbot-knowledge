---
type: API
title: GlobalTensor简介
description: GlobalTensor用来存放Global Memory（外部存储）的全局数据。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/GlobalTensor_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# GlobalTensor简介

GlobalTensor 用于存放 Global Memory（外部存储）的全局数据。通过 SetGlobalBuffer 设置 GM 地址和大小，通过 GetValue/SetValue 读写元素，GetShapeInfo/SetShapeInfo 管理形状，GetPhyAddr 获取物理地址，GetTotalSize/GetSize 获取大小。支持 ReinterpretCast 类型重解释和 operator[] 下标访问。SetL2CacheHint 可设置 L2 Cache 策略。

<!-- cannbot:related:start -->
## 相关

- [GetShapeInfo](get_shape_info.md)（`related`）：GetShapeInfo 与《GlobalTensor简介》的实质衔接是：GetShapeInfo 只有在对应 GlobalTensor 已 SetShapeInfo 后才有效；ShapeInfo、SetGlobalBuffer 与 tensor 子视图共同约束 shape 元数据生命周期。
- [SetGlobalBuffer](set_global_buffer.md)（`related`）：《SetGlobalBuffer》明确“传入全局数据地址，初始化GlobalTensor。”；它与《GlobalTensor简介》的“GlobalTensor用来存放Global Memory（外部存储）的全局数据。”在实际调用参数、数据流或结果校验上直接衔接。
- [GlobalTensor构造函数](global_tensor_constructor.md)（`same_topic`）：《GlobalTensor构造函数》明确“GlobalTensor构造函数。”；它与《GlobalTensor简介》的“GlobalTensor用来存放Global Memory（外部存储）的全局数据。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
