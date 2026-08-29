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

- [DataCopyPad（UBToL1非对齐数据搬运）](data_copy_pad_ub_to_l1.md)（`same_topic`）：“将Unified Buffer中的数据搬运到L1 Buffer，支持在搬运过程中对数据进行Padding。用于源数据长度不满足对齐要求时自动补齐。”与“将Unified Buffer中的连续数据搬运到L1 Buffer，数据格式不变。用于从Vector侧向Cube侧传递数据。”是双方正文中的具体合同。两端都是 UB 到 L1 的 Vector→Cube 搬运合同，差别在源长度是否需要 Padding；互读能直接决定对齐输入使用连续搬运还是带补齐搬运。
<!-- cannbot:related:end -->
