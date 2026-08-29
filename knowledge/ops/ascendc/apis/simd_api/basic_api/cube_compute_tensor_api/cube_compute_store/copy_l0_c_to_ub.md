---
type: API
title: Copy
description: 将L0C Buffer中的矩阵计算结果搬运到Unified Buffer，支持随路格式转换、量化输出、Relu和batch模式等特性。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_compute_store/Copy_L0CToUB.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# Copy（L0C到UB数据搬运）

通过统一Copy接口将L0C Buffer数据搬运到Unified Buffer，用于矩阵计算结果在Vector侧进一步处理。搬运参数由Tensor Layout自动推导。仅Ascend 950PR/950DT支持。试验接口。

支持场景：连续数据搬出、随路格式转换、双目的搬出（L0CToUBDualDst，同时搬出到两个UB地址）。函数原型通过模板参数指定AtomType、DstTensor和SrcTensor类型。约束：遵循Cube计算地址对齐约束。头文件：tensor_api/tensor.h。

<!-- cannbot:related:start -->
## 相关

- [基础API随路量化](../cube_store_key_features/quant_pre.md)（`related`）：随路量化是矩阵计算结果从L0C Buffer搬出到Global Memory或Unified Buffer过程中的数据转换能力。；通过统一Copy接口将L0C Buffer数据搬运到Unified Buffer，用于矩阵计算结果在Vector侧进一步处理。；候选给出 QuantPre 的另一条 L0C 到 UB 输出消费路径。
<!-- cannbot:related:end -->
