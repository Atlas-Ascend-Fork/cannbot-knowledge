---
type: API
title: SetHF32Mode
description: 用于设置Mmad计算是否开启HF32模式，开启该模式后L0A Buffer/L0B Buffer中的FP32数据将在参与Mmad计算之前被舍入为HF32。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute_aux_config/SetHF32Mode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetHF32Mode

设置 Mmad 计算是否开启 HF32 模式。开启后 L0A Buffer/L0B Buffer 中的 FP32 数据将在参与 Mmad 计算前被舍入为 HF32（half-fp32），可使 f322f32 计算性能提升 2 倍，但有精度损失。

参数：mode 为 HF32Mode 枚举，ENABLE 开启舍入、DISABLE 执行常规 FP32 矩阵乘。舍入方式通过 SetHF32TransMode 配置。支持 950/a2/a3/Atlas 200I/500 A2，不支持 Atlas 推理/训练系列。

<!-- cannbot:related:start -->
## 相关

- [AscEnableHf32](../../../c_api/cube_compute/asc_enable_hf32.md)（`related`）：AscEnableHf32 与《SetHF32Mode》的实质衔接是：HF32 开关与转置开关、舍入模式和 C/C++ 配置入口共同决定 Cube FP32 的计算模式，特性页解释性能精度权衡。
- [AscMmad](../../../c_api/cube_compute/asc_mmad.md)（`related`）：AscMmad 与《SetHF32Mode》的实质衔接是：AscMmad 在 AIC 上消费 L0A/L0B 并累加到 L0C；Mmad 约束、方向/HF32 配置、Cube 流程和 AIV 误调用故障共同覆盖实际调用边界。
- [AscSetFp32Mode](../../../c_api/cube_compute/asc_set_fp32_mode.md)（`related`）：AscSetFp32Mode 与《SetHF32Mode》的实质衔接是：AscSetFp32Mode 与 HF32 round/enable/trans 配置共同决定 AscMmad 的 FP32/HF32 计算模式，Mmad 约束和 HF32 指南说明精度与方向设置。
- [AscSetHf32RoundMode](../../../c_api/cube_compute/asc_set_hf32_round_mode.md)（`related`）：《AscSetHf32RoundMode》说明设置HF32模式舍入方式。使用该接口前需要先使用asc_enable_hf32开启HF32模式。；《SetHF32Mode》说明用于设置Mmad计算是否开启HF32模式，开启该模式后L0A Buffer/L0B Buffer中的FP32数据将在参与Mmad计算之前被舍入为HF32。。二者在HF32舍入模式只有在HF32/Trans开启后生效，枚举、基础API、Matmul API和关闭FP32模式共同界定状态机上存在可执行的直接衔接。
- [Cube计算(ISASI)HF32](../mmad_compute_key_features/hf32.md)（`related`）：SetHF32Mode 控制 HF32 计算是否启用，是特性页落地的直接开关。
- [Mmad计算关键特性说明](../../cube_compute_tensor_api/mmad_compute_key_features/mmad_compute_key_features.md)（`related`）：关键特性页描述 HF32 的性能/精度权衡，SetHF32Mode 是真正启停该舍入行为的配置接口，并指向独立舍入方式设置。
- [SetHF32](../../../adv_api/cube_compute/matmul_kernel/set_hf32.md)（`related`）：基础 MMAD 的 SetHF32Mode 与 Matmul 高阶 SetHF32 都控制 fp32→HF32 性能/精度取舍，但作用接口层不同。
- [SetHF32TransMode](set_hf32_trans_mode.md)（`related`）：SetHF32Mode 控制 HF32 计算开关，SetHF32TransMode 控制转换模式；二者共同决定 fp32 到 HF32 的 Mmad 行为。
- [AscHf32RoundMode](../../../c_api/enum/asc_hf32_round_mode.md)（`same_topic`）：《AscHf32RoundMode》处理“用于Mmad计算开启HF32模式时FP32到HF32的舍入模式管理策略，在调用asc_set_hf32_round_mode时使用。”。《SetHF32Mode》明确“用于设置Mmad计算是否开启HF32模式，开启该模式后L0A Buffer/L0B Buffer中的FP32数据将在参与Mmad计算之前被舍入为HF32。”，可直接用于核对HF32 rounding/trans mode 的配置入口及其对 Mmad 执行精度的直接影响。
<!-- cannbot:related:end -->
