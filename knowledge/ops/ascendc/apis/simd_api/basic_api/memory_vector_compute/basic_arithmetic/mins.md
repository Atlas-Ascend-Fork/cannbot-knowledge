---
type: API
title: Mins
description: 双目矢量标量计算接口，将矢量tensor每个元素与标量取最小值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Mins.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Mins

标量矢量计算接口，每个元素与标量取最小值。头文件 `basic_api/kernel_operator_vec_binary_intf.h`。计算公式 dst_i = min(src_i, scalarValue)。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [Maxs 下限 clamp 阻止 exp 自然下溢残留](../../../../../runbooks/precision/maxs_clamp_exp.md)（`exemplifies`）：Mins 与《Maxs 下限 clamp 阻止 exp 自然下溢残留》的实质衔接是：Mins 是 tensor 与标量逐元素取小值；Reg/灵活标量入口保持同一契约，Maxs/Min/Relu 组合及 exp clamp 案例说明它作为上界限幅的实际语义。
- [SoftplusV2Grad VF Form B exp 溢出判别](../../../../../runbooks/precision/softplusv2grad_vf_form_b_exp.md)（`exemplifies`）：Mins 与《SoftplusV2Grad VF Form B exp 溢出判别》的实质衔接是：Mins 是 tensor 与标量逐元素取小值；Reg/灵活标量入口保持同一契约，Maxs/Min/Relu 组合及 exp clamp 案例说明它作为上界限幅的实际语义。
- [exp 下界 clamp -50 破坏 sigmoid 大负数下溢](../../../../../runbooks/precision/exp_clamp_50_sigmoid.md)（`exemplifies`）：Mins 与《exp 下界 clamp -50 破坏 sigmoid 大负数下溢》的实质衔接是：Mins 是 tensor 与标量逐元素取小值；Reg/灵活标量入口保持同一契约，Maxs/Min/Relu 组合及 exp clamp 案例说明它作为上界限幅的实际语义。
- [exp 输入 clamp 上界用 threshold 用户参数致溢出](../../../../../runbooks/precision/exp_clamp_upper_bound_must_decouple_from_user_threshold.md)（`exemplifies`）：exp 输入 clamp 上界用 threshold 用户参数致溢出 与《Mins》的实质衔接是：故障由用户 threshold 充当 Exp 安全上界导致；Exp、Clamp/Mins、Sigmoid 公式及溢出/FTZ/Softplus 分支案例共同限定固定上界和极值验收。
- [LeakyRelu](leaky_relu.md)（`related`）：LeakyRelu 与《Mins》的实质衔接是：LeakyRelu 的负分支乘 alpha、非负分支保留原值，可由 Muls 与 Maxs/Mins 组合；Prelu、Relu 及 C/Reg 入口给出相同或退化调用语义。
- [Mins](../../reg_vector_compute/basic_arithmetic/mins.md)（`related`）：Memory Vector 的 Mins 实现同一标量最小值语义，但数据位于 LocalTensor，便于在两种编程模型间选型。
- [Relu](relu.md)（`related`）：Mins 与《Relu》的实质衔接是：Mins 是 tensor 与标量逐元素取小值；Reg/灵活标量入口保持同一契约，Maxs/Min/Relu 组合及 exp clamp 案例说明它作为上界限幅的实际语义。
- [Maxs](maxs.md)（`same_topic`）：Maxs 与《Mins》的实质衔接是：Maxs 是 tensor 与标量逐元素取大值；Reg/灵活标量入口保持同一契约，Mins/Relu/LeakyRelu 以及 exp clamp 案例说明它在分段和限幅公式中的实际组合。
- [Min](min.md)（`same_topic`）：Mins 与《Min》的实质衔接是：Mins 是 tensor 与标量逐元素取小值；Reg/灵活标量入口保持同一契约，Maxs/Min/Relu 组合及 exp clamp 案例说明它作为上界限幅的实际语义。
- [Mins（灵活标量位置）](mins_flexible_scalar.md)（`same_topic`）：Mins 与《Mins（灵活标量位置）》的实质衔接是：Mins 是 tensor 与标量逐元素取小值；Reg/灵活标量入口保持同一契约，Maxs/Min/Relu 组合及 exp clamp 案例说明它作为上界限幅的实际语义。
<!-- cannbot:related:end -->
