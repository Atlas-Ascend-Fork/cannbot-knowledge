---
type: API
title: IsBasicBlockInSoftMax
description: 用于判断SoftMaxTiling结构是否符合基本块特征。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/SoftMax_interface/IsBasicBlockInSoftMax.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# IsBasicBlockInSoftMax

用于判断SoftMaxTiling结构是否符合基本块特征。

参数：
- 接口（输入 输出）：功能
- tiling（输入）：待判断的SoftMaxTiling结构，支持optiling::SoftMaxTiling形式入参和AscendC::tiling::SoftMaxTiling形式入参。
- dataTypeSize（输入）：参与计算的srcTensor的数据类型大小，比如half=2。

返回值：- 返回true表示SoftMaxTiling结构满足基本块Tiling特征。
