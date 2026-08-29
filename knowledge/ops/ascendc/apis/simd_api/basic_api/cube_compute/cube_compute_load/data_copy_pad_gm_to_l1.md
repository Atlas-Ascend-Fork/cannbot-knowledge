---
type: API
title: DataCopyPad（GMToL1非对齐数据搬运）
description: 该接口提供从Global Memory到L1 Buffer的数据非对齐搬运功能，可以根据开发者的需要自行填充数据。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopyPad_GMToL1.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# DataCopyPad（GM到L1带Padding搬运）

将Global Memory中的数据搬运到L1 Buffer，支持在搬运过程中对数据进行Padding（补齐）。用于源数据长度不满足对齐要求时自动补齐。

函数原型通过模板参数指定数据类型。参数包含dstTensor、srcTensor、dataCopyParams、padParams（含padding值和方向）。约束：遵循Cube计算地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [SIMD算子实现分离模式](../../../../../guides/operator_practice/simd_operator_impl/matrix_basic_api/decoupled_mode.md)（`explains`）：分离模式 Matmul 规格要求“DataCopy（GMToL1随路转换-ND2NZ搬运）：Global Memory到L1 Buffer数据搬运 + ND转NZ格式转换接口”；DataCopyPad 页定义“将Global Memory中的数据搬运到L1 Buffer，支持在搬运过程中对数据进行Padding（补齐）。”，后者是非对齐输入进入前者 GM→L1 阶段的具体实现选择。
<!-- cannbot:related:end -->
