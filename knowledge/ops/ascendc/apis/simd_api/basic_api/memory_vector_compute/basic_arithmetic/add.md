---
type: API
title: Add
description: 双目矢量计算接口，对两个输入tensor按元素求和。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Add.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Add

双目矢量计算接口，按元素求和。头文件 `basic_api/kernel_operator_vec_binary_intf.h`。计算公式 dst_i = src0_i + src1_i。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [Add算子快速入门](../../../../../guides/getting_started/quick_start/simd_programming/add_op_quick_start.md)（`explains`）：快速入门的 C++ 路径在 Compute 阶段直接调用 AscendC::Add 完成 z=x+y；API 卡给出逐元素语义，是样例计算核心的精确接口。
- [Add](../../reg_vector_compute/basic_arithmetic/add.md)（`related`）：Add 与《Add》的实质衔接是：Reg Add 与 C API Add 实现相同逐 lane 加法；complex32/64 是该接口支持复数重载时所需的操作数契约。
- [Adds](adds.md)（`related`）：Add 对两个 tensor 逐元素求和，Adds 对 tensor 与 scalar 求和；选择取决于第二操作数是否需要物化为 tensor。
- [BilinearInterpolation](bilinear_interpolation_isasi.md)（`related`）：双线性插值需合并四邻域加权结果，Add 是下游组合步骤而非完整插值接口。
<!-- cannbot:related:end -->
