---
type: API
title: DataCopy
description: 随路格式转换数据搬运，将数据从Global Memory搬运至L1 Buffer（TPosition为A1/B1），搬运过程中完成DN到NZ格式转换。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopy_GMToL1_DN2NZ.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# DataCopy（GM到L1 DN2NZ格式转换）

将Global Memory中的DN格式数据搬运到L1 Buffer并转换为NZ格式。用于矩阵计算输入的随路格式转换搬入。

函数原型通过模板参数指定数据类型。参数包含dstTensor（L1目的NZ格式）、srcTensor（GM源DN格式）、dataCopyParams（搬运参数含源/目的shape等）。约束：源/目的地址需满足对齐要求；遵循Cube计算格式转换约束。

<!-- cannbot:related:start -->
## 相关

- [AscCopyGm2l1Dn2nz](../../../c_api/cube_data_move/asc_copy_gm2l1_dn2nz.md)（`same_topic`）：将矩阵数据从Global Memory搬运到L1 Buffer，在此过程中执行DN->NZ/NCHW->NC1HWC0/NCHW->C1HWNC0操作。若D未对齐C0的大小，将会在L1 Buffer的最内层维度填充0值。GM中的数据以DN类型存储；L1中的数据以NZ形式存储。；将Global Memory中的DN格式数据搬运到L1 Buffer并转换为NZ格式。用于矩阵计算输入的随路格式转换搬入。。两卡描述同一 GM 到 L1 的 DN→NZ 搬运，在 C API 与 Basic API 中提供不同调用表面。
<!-- cannbot:related:end -->
