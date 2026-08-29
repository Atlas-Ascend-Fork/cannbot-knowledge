---
type: API
title: Log
description: 根据mask逐元素对源操作数求自然对数（以e为底），将结果写入目的操作数。功能与Ln接口等价，命名遵循C/C++标准库log()约定。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/Log.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Log

根据mask逐元素对源操作数求自然对数（以e为底），将结果写入目的操作数。功能与Ln接口等价，命名遵循C/C++标准库log()约定。

头文件路径："basic_api/reg_compute/kernel_reg_compute_vec_unary_intf.h"。 该接口根据mask逐元素对源操作数求自然对数，将结果写入目的操作数。计算公式如下：

本接口组包含 Ln, MaskMergeMode, RegTensor, RegTensor, MaskReg。

本接口属于 Reg 矢量计算基础算术接口，操作 RegTensor 寄存器数据，直接在寄存器级别执行矢量运算。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Ln](ln.md)（`same_topic`）：功能与Ln接口等价，命名遵循C/C++标准库log()约定。；根据mask逐元素对源操作数求自然对数，将结果写入目的操作数。；两端是同一 RegTensor 自然对数运算的等价命名。
<!-- cannbot:related:end -->
