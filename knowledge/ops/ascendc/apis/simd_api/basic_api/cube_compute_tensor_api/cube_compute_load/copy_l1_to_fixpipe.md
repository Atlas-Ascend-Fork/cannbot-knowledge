---
type: API
title: CopyL1ToFixpipe
description: 通过Tensor API的Copy接口将L1 Buffer中的量化数据搬运到Fixpipe Buffer，用于L0C输出时随路量化。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_compute_load/Copy_L1ToFixpipe.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# Copy（L1到Fixpipe数据搬运）

通过统一Copy接口将L1 Buffer数据搬运到Fixpipe，用于矩阵计算中Fixpipe数据处理。搬运参数由Tensor Layout自动推导。仅Ascend 950PR/950DT支持。试验接口。

函数原型通过模板参数指定AtomType、DstTensor和SrcTensor类型。约束：遵循Cube计算地址对齐约束。头文件：tensor_api/tensor.h。

<!-- cannbot:related:start -->
## 相关

- [基础API随路量化](../cube_store_key_features/quant_pre.md)（`related`）：tensor量化参数张量应位于L1 Buffer，元素类型为uint64_t，地址要求32字节对齐。；通过统一Copy接口将L1 Buffer数据搬运到Fixpipe，用于矩阵计算中Fixpipe数据处理。；候选是 L1 量化参数进入 Fixpipe 的生产消费步骤。
<!-- cannbot:related:end -->
