---
type: API
title: TransDataTo5HD
description: 将NCHW格式转换为NC1HWC0格式，也可用于二维矩阵数据块转置，单次repeat可处理512字节数据。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_layout_conversion/TransDataTo5HD.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TransDataTo5HD

数据格式转换接口，将数据转换为 5HD（NC1HWC0）格式。头文件 `basic_api/kernel_operator_vec_intf.h`。支持 950/a2/a3。
