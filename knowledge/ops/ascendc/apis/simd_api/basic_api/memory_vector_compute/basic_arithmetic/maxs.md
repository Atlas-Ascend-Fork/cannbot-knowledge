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

- [Maxs 下限 clamp 阻止 exp 自然下溢残留](../../../../../runbooks/precision/maxs_clamp_exp.md)（`exemplifies`）：Maxs 与《Maxs 下限 clamp 阻止 exp 自然下溢残留》的实质衔接是：Maxs 是 tensor 与标量逐元素取大值；Reg/灵活标量入口保持同一契约，Mins/Relu/LeakyRelu 以及 exp clamp 案例说明它在分段和限幅公式中的实际组合。
- [LeakyRelu](leaky_relu.md)（`related`）：Maxs 与《LeakyRelu》的实质衔接是：Maxs 是 tensor 与标量逐元素取大值；Reg/灵活标量入口保持同一契约，Mins/Relu/LeakyRelu 以及 exp clamp 案例说明它在分段和限幅公式中的实际组合。
- [Mins（灵活标量位置）](mins_flexible_scalar.md)（`related`）：Maxs 与《Mins（灵活标量位置）》的实质衔接是：Maxs 是 tensor 与标量逐元素取大值；Reg/灵活标量入口保持同一契约，Mins/Relu/LeakyRelu 以及 exp clamp 案例说明它在分段和限幅公式中的实际组合。
- [Relu](relu.md)（`related`）：Maxs 与《Relu》的实质衔接是：Maxs 是 tensor 与标量逐元素取大值；Reg/灵活标量入口保持同一契约，Mins/Relu/LeakyRelu 以及 exp clamp 案例说明它在分段和限幅公式中的实际组合。
- [Max](max.md)（`same_topic`）：Maxs 将第二操作数改为标量，按 tensor/tensor 或 tensor/scalar 需求选用。
- [Maxs](../../reg_vector_compute/basic_arithmetic/maxs.md)（`same_topic`）：Maxs 与《Maxs》的实质衔接是：Maxs 是 tensor 与标量逐元素取大值；Reg/灵活标量入口保持同一契约，Mins/Relu/LeakyRelu 以及 exp clamp 案例说明它在分段和限幅公式中的实际组合。
- [Maxs（灵活标量位置）](maxs_flexible_scalar.md)（`same_topic`）：Maxs 与《Maxs（灵活标量位置）》的实质衔接是：Maxs 是 tensor 与标量逐元素取大值；Reg/灵活标量入口保持同一契约，Mins/Relu/LeakyRelu 以及 exp clamp 案例说明它在分段和限幅公式中的实际组合。
- [Mins](mins.md)（`same_topic`）：Maxs 与《Mins》的实质衔接是：Maxs 是 tensor 与标量逐元素取大值；Reg/灵活标量入口保持同一契约，Mins/Relu/LeakyRelu 以及 exp clamp 案例说明它在分段和限幅公式中的实际组合。
<!-- cannbot:related:end -->
