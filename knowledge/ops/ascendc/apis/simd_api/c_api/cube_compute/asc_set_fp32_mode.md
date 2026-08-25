---
type: API
title: AscSetFp32Mode
description: 本接口用于设置Mmad计算关闭HF32模式，其作用与asc_enable_hf32相反，两个接口不同时生效。关闭HF32模式后，L0A Buffer与L0B
  Buffer中的float数据在参与Mmad计算之前不做舍入处理。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_compute/asc_set_fp32_mode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscSetFp32Mode

本接口用于设置Mmad计算关闭HF32模式，其作用与asc_enable_hf32相反，两个接口不同时生效。关闭HF32模式后，L0A Buffer与L0B Buffer中的float数据在参与Mmad计算之前不做舍入处理。

约束：- 本接口需在矩阵乘加指令（asc_mmad）执行前调用，以此来确保模式配置在矩阵乘加计算过程中生效。
- FP32模式启用后会持续生效，不会自动关闭。后续矩阵乘加指令若不显式重新配置，将沿用当前模式。如需开启HF32模式，请重新调用asc_enable_hf32接口。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscMmad](asc_mmad.md)（`related`）：AscSetFp32Mode 与《AscMmad》的实质衔接是：AscSetFp32Mode 与 HF32 round/enable/trans 配置共同决定 AscMmad 的 FP32/HF32 计算模式，Mmad 约束和 HF32 指南说明精度与方向设置。
- [Cube计算(ISASI)HF32](../../basic_api/cube_compute/mmad_compute_key_features/hf32.md)（`related`）：AscSetFp32Mode 与《Cube计算(ISASI)HF32》的实质衔接是：AscSetFp32Mode 与 HF32 round/enable/trans 配置共同决定 AscMmad 的 FP32/HF32 计算模式，Mmad 约束和 HF32 指南说明精度与方向设置。
- [Mmad接口边界值汇总](../../../appendix/mmad_interface_boundary_value_summary.md)（`related`）：AscSetFp32Mode 与《Mmad接口边界值汇总》的实质衔接是：AscSetFp32Mode 与 HF32 round/enable/trans 配置共同决定 AscMmad 的 FP32/HF32 计算模式，Mmad 约束和 HF32 指南说明精度与方向设置。
- [Mmad辅助配置说明](../../basic_api/cube_compute/mmad_compute_aux_config/mmad_compute_aux_config.md)（`related`）：AscSetFp32Mode 与《Mmad辅助配置说明》的实质衔接是：AscSetFp32Mode 与 HF32 round/enable/trans 配置共同决定 AscMmad 的 FP32/HF32 计算模式，Mmad 约束和 HF32 指南说明精度与方向设置。
- [SetHF32Mode](../../basic_api/cube_compute/mmad_compute_aux_config/set_hf32_mode.md)（`related`）：AscSetFp32Mode 与《SetHF32Mode》的实质衔接是：AscSetFp32Mode 与 HF32 round/enable/trans 配置共同决定 AscMmad 的 FP32/HF32 计算模式，Mmad 约束和 HF32 指南说明精度与方向设置。
- [基础APIHF32](../../basic_api/cube_compute_tensor_api/mmad_compute_key_features/hf32.md)（`related`）：AscSetFp32Mode 与《基础APIHF32》的实质衔接是：AscSetFp32Mode 与 HF32 round/enable/trans 配置共同决定 AscMmad 的 FP32/HF32 计算模式，Mmad 约束和 HF32 指南说明精度与方向设置。
- [AscEnableHf32](asc_enable_hf32.md)（`same_topic`）：AscSetFp32Mode 与《AscEnableHf32》的实质衔接是：AscSetFp32Mode 与 HF32 round/enable/trans 配置共同决定 AscMmad 的 FP32/HF32 计算模式，Mmad 约束和 HF32 指南说明精度与方向设置。
- [AscEnableHf32Trans](asc_enable_hf32_trans.md)（`same_topic`）：AscSetFp32Mode 与《AscEnableHf32Trans》的实质衔接是：AscSetFp32Mode 与 HF32 round/enable/trans 配置共同决定 AscMmad 的 FP32/HF32 计算模式，Mmad 约束和 HF32 指南说明精度与方向设置。
- [AscHf32RoundMode](../enum/asc_hf32_round_mode.md)（`same_topic`）：《AscHf32RoundMode》处理“用于Mmad计算开启HF32模式时FP32到HF32的舍入模式管理策略，在调用asc_set_hf32_round_mode时使用。”。《AscSetFp32Mode》明确“本接口用于设置Mmad计算关闭HF32模式，其作用与asc_enable_hf32相反，两个接口不同时生效。关闭HF32模式后，L0A Buffer与L0B Buffer中的float数据在参与Mmad计算之前不做舍入处理。”，可直接用于核对HF32 rounding/trans mode 的配置入口及其对 Mmad 执行精度的直接影响。
- [AscSetHf32RoundMode](asc_set_hf32_round_mode.md)（`same_topic`）：AscSetFp32Mode 与《AscSetHf32RoundMode》的实质衔接是：AscSetFp32Mode 与 HF32 round/enable/trans 配置共同决定 AscMmad 的 FP32/HF32 计算模式，Mmad 约束和 HF32 指南说明精度与方向设置。
- [矩阵计算](cube_compute.md)（`same_topic`）：AscSetFp32Mode 与《矩阵计算》的实质衔接是：AscSetFp32Mode 与 HF32 round/enable/trans 配置共同决定 AscMmad 的 FP32/HF32 计算模式，Mmad 约束和 HF32 指南说明精度与方向设置。
<!-- cannbot:related:end -->
