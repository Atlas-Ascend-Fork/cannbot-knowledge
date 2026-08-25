---
type: API
title: AscEnableHf32Trans
description: 设置HF32模式舍入方式。使用该接口前需要先使用asc_enable_hf32开启HF32模式。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_compute/asc_enable_hf32_trans.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscEnableHf32Trans

设置HF32模式舍入方式。使用该接口前需要先使用asc_enable_hf32开启HF32模式。

参数：mode(输入): HF32取整模式控制入参，uint32_t类型，支持如下2种取值： 0：FP32将以最接近偶数的方式四舍五入为HF32。 1：FP32将以向零靠近的方式四。

约束：mode仅支持如下2种取值： 0：FP32将以最接近偶数的方式四舍五入为HF32。 1：FP32将以向零靠近的方式四舍五入为HF32。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscEnableHf32](asc_enable_hf32.md)（`same_topic`）：AscEnableHf32Trans 与《AscEnableHf32》的实质衔接是：AscEnableHf32Trans 只能在启用 HF32 后设置舍入；C++ 对应配置、round mode 枚举和 HF32 指南共同决定 Cube FP32 的精度模式。
- [AscHf32RoundMode](../enum/asc_hf32_round_mode.md)（`same_topic`）：《AscHf32RoundMode》处理“用于Mmad计算开启HF32模式时FP32到HF32的舍入模式管理策略，在调用asc_set_hf32_round_mode时使用。”。《AscEnableHf32Trans》明确“设置HF32模式舍入方式。使用该接口前需要先使用asc_enable_hf32开启HF32模式。”，可直接用于核对HF32 rounding/trans mode 的配置入口及其对 Mmad 执行精度的直接影响。
- [AscSetFp32Mode](asc_set_fp32_mode.md)（`same_topic`）：AscSetFp32Mode 与《AscEnableHf32Trans》的实质衔接是：AscSetFp32Mode 与 HF32 round/enable/trans 配置共同决定 AscMmad 的 FP32/HF32 计算模式，Mmad 约束和 HF32 指南说明精度与方向设置。
- [AscSetHf32RoundMode](asc_set_hf32_round_mode.md)（`same_topic`）：《AscSetHf32RoundMode》说明设置HF32模式舍入方式。使用该接口前需要先使用asc_enable_hf32开启HF32模式。；《AscEnableHf32Trans》说明设置HF32模式舍入方式。使用该接口前需要先使用asc_enable_hf32开启HF32模式。。二者在HF32舍入模式只有在HF32/Trans开启后生效，枚举、基础API、Matmul API和关闭FP32模式共同界定状态机上存在可执行的直接衔接。
- [Cube计算(ISASI)HF32](../../basic_api/cube_compute/mmad_compute_key_features/hf32.md)（`same_topic`）：AscEnableHf32Trans 与《Cube计算(ISASI)HF32》的实质衔接是：AscEnableHf32Trans 只能在启用 HF32 后设置舍入；C++ 对应配置、round mode 枚举和 HF32 指南共同决定 Cube FP32 的精度模式。
- [SetHF32TransMode](../../basic_api/cube_compute/mmad_compute_aux_config/set_hf32_trans_mode.md)（`same_topic`）：AscEnableHf32Trans 与《SetHF32TransMode》的实质衔接是：AscEnableHf32Trans 只能在启用 HF32 后设置舍入；C++ 对应配置、round mode 枚举和 HF32 指南共同决定 Cube FP32 的精度模式。
- [基础APIHF32](../../basic_api/cube_compute_tensor_api/mmad_compute_key_features/hf32.md)（`same_topic`）：AscEnableHf32Trans 与《基础APIHF32》的实质衔接是：AscEnableHf32Trans 只能在启用 HF32 后设置舍入；C++ 对应配置、round mode 枚举和 HF32 指南共同决定 Cube FP32 的精度模式。
<!-- cannbot:related:end -->
