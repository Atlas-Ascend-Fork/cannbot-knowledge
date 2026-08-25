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
