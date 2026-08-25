---
type: API
title: ToFile
description: 只限于CPU调试，将LocalTensor数据Dump到文件中，用于精度调试，文件保存在执行目录。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/ToFile.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# ToFile

只限于CPU调试，将LocalTensor数据Dump到文件中，用于精度调试，文件保存在执行目录。

只限于CPU调试，将LocalTensor数据Dump到文件中，用于精度调试，文件保存在执行目录。

本接口属于 LocalTensor 数据结构操作接口，用于访问和修改 UB 上的 Tensor 属性。

返回值：返回0表示数据Dump成功，非0值表示失败。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。
