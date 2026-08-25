---
type: API
title: DataCopy
description: 将矩阵从Unified Buffer搬运至L1 Buffer，采用连续搬运方式，数据搬运时格式和内容保持不变。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopy_UBToL1_continuous.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# DataCopy（UB到L1连续搬运）

将Unified Buffer中的连续数据搬运到L1 Buffer，数据格式不变。用于从Vector侧向Cube侧传递数据。

函数原型通过模板参数指定数据类型。参数包含dstTensor（L1目的）、srcTensor（UB源）、dataCopyParams。约束：遵循Cube计算地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [DataCopy](data_copy_ub_to_l1_highdim_split.md)（`related`）：两者数据路径同为 UB 到 L1；连续版用于一段连续矩阵，高维切分版增加分段与 stride 描述，提供按布局选择搬运重载的边界。
<!-- cannbot:related:end -->
