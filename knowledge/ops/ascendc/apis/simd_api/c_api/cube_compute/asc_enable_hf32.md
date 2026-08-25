---
type: API
title: AscEnableHf32
description: 设置Mmad计算开启HF32模式，开启后Mmad计算FP32数据性能提升但会带来一定精度损失。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_compute/asc_enable_hf32.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscEnableHf32

本接口用于设置Mmad计算开启HF32模式，开启该模式后，Mmad计算FP32数据的性能将得到提升，但会带来一定的精度损失。

是否开启HF32对Mmad计算理论性能的影响

性能关键变量及常量说明
- ：mmad入参实际计算的大小。
- ： 根据分形大小向上对齐后的值。
- ：硬件真实并行度（单位：elements/cycle）。
- ：L0 Buffer上最小分形K方向大小。
- ：头开销cycle数。

开启HF32模式后，L0A Buffer/L0B Buffer中的FP32数据将在参与Mmad计算之前被舍入为HF32格式，舍入模式使用asc_set_hf32_round_mode接口配置，中间计算使用HF32格式，最终的运算结果仍以FP32格式输出，以保证后续处理的兼容性。

FP32与HF32格式的精度对比如下图所示

约束：- 本接口需在矩阵乘加指令（asc_mmad）执行前调用，以此来确保模式配置在矩阵乘加计算过程中生效。
- HF32模式启用后会持续生效，不会自动关闭。后续矩阵乘加指令若不显式重新配置，将沿用当前模式。如需关闭HF32模式，请重新调用asc_set_fp32_mode接口。
- HF32模式启用后，FP32转换为HF32格式的舍入模式由配套的asc_set_hf32_round_mode接口配置，须在本接口之后调用该配套接口配置舍入模式，否则舍入模式沿用上次配置或默认值。
- HF32模式仅对输入矩阵数据类型为float的矩阵乘加运算场景生效。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscSetHf32RoundMode](asc_set_hf32_round_mode.md)（`related`）：《AscSetHf32RoundMode》说明设置HF32模式舍入方式。使用该接口前需要先使用asc_enable_hf32开启HF32模式。；《AscEnableHf32》说明设置Mmad计算开启HF32模式，开启后Mmad计算FP32数据性能提升但会带来一定精度损失。。二者在HF32舍入模式只有在HF32/Trans开启后生效，枚举、基础API、Matmul API和关闭FP32模式共同界定状态机上存在可执行的直接衔接。
- [Cube计算(ISASI)HF32](../../basic_api/cube_compute/mmad_compute_key_features/hf32.md)（`related`）：AscEnableHf32 与《Cube计算(ISASI)HF32》的实质衔接是：HF32 开关与转置开关、舍入模式和 C/C++ 配置入口共同决定 Cube FP32 的计算模式，特性页解释性能精度权衡。
- [SetHF32](../../adv_api/cube_compute/matmul_kernel/set_hf32.md)（`related`）：AscEnableHf32 与《SetHF32》的实质衔接是：HF32 开关与转置开关、舍入模式和 C/C++ 配置入口共同决定 Cube FP32 的计算模式，特性页解释性能精度权衡。
- [SetHF32Mode](../../basic_api/cube_compute/mmad_compute_aux_config/set_hf32_mode.md)（`related`）：AscEnableHf32 与《SetHF32Mode》的实质衔接是：HF32 开关与转置开关、舍入模式和 C/C++ 配置入口共同决定 Cube FP32 的计算模式，特性页解释性能精度权衡。
- [SetHF32TransMode](../../basic_api/cube_compute/mmad_compute_aux_config/set_hf32_trans_mode.md)（`related`）：AscEnableHf32 与《SetHF32TransMode》的实质衔接是：HF32 开关与转置开关、舍入模式和 C/C++ 配置入口共同决定 Cube FP32 的计算模式，特性页解释性能精度权衡。
- [AscEnableHf32Trans](asc_enable_hf32_trans.md)（`same_topic`）：AscEnableHf32Trans 与《AscEnableHf32》的实质衔接是：AscEnableHf32Trans 只能在启用 HF32 后设置舍入；C++ 对应配置、round mode 枚举和 HF32 指南共同决定 Cube FP32 的精度模式。
- [AscHf32RoundMode](../enum/asc_hf32_round_mode.md)（`same_topic`）：《AscHf32RoundMode》处理“用于Mmad计算开启HF32模式时FP32到HF32的舍入模式管理策略，在调用asc_set_hf32_round_mode时使用。”。《AscEnableHf32》明确“设置Mmad计算开启HF32模式，开启后Mmad计算FP32数据性能提升但会带来一定精度损失。”，可直接用于核对HF32 rounding/trans mode 的配置入口及其对 Mmad 执行精度的直接影响。
- [AscSetFp32Mode](asc_set_fp32_mode.md)（`same_topic`）：AscSetFp32Mode 与《AscEnableHf32》的实质衔接是：AscSetFp32Mode 与 HF32 round/enable/trans 配置共同决定 AscMmad 的 FP32/HF32 计算模式，Mmad 约束和 HF32 指南说明精度与方向设置。
<!-- cannbot:related:end -->
