---
type: API
title: Maxs
description: 双目矢量标量计算接口，将矢量tensor每个元素与标量取最大值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Maxs.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Maxs

标量矢量计算接口，每个元素与标量取最大值。头文件 `basic_api/kernel_operator_vec_binary_intf.h`。计算公式 dst_i = max(src_i, scalarValue)。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [ForeachMaximumScalar A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_maximum_scalar.md)（`related`）：A2/A3 算子卡的实际路由包含“FLOAT32 -> key 2 -> ForeachOneScalarBinary<float, float, MaxsAdapter<float>, 2>”；Maxs 卡定义“计算公式 dst_i = max(src_i, scalarValue)。”，后者直接解释 Foreach 内核每个张量 tile 的标量最大值 primitive。
- [InplaceHardtanh 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/inplace_hardtanh_950.md)（`related`）：Maxs(yLocal, xLocal, minValue, len)；标量矢量计算接口，每个元素与标量取最大值。头文件 `basic_api/kernel_operator_vec_binary_intf.h`。计算公式 dst_i = max(src_i, scalarValue)。算子 kernel 直接以 Maxs 实现 Hardtanh 下界裁剪。
<!-- cannbot:related:end -->
