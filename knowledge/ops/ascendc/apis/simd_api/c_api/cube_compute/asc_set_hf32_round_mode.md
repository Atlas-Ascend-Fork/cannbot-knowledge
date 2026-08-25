---
type: API
title: AscSetHf32RoundMode
description: 设置HF32模式舍入方式。使用该接口前需要先使用asc_enable_hf32开启HF32模式。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_compute/asc_set_hf32_round_mode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscSetHf32RoundMode

设置HF32模式舍入方式。使用该接口前需要先使用asc_enable_hf32开启HF32模式。

参数：hf32_round_mode(输入): HF32舍入模式控制入参，asc_hf32_round_mode枚举类型，支持如下2种枚举值： &nbsp;&nbsp;&bull; NEAREST_ZE。

约束：hf32_round_mode仅支持如下2种枚举值
- asc_hf32_round_mode::NEAREST_ZERO
- asc_hf32_round_mode::NEAREST_EVEN

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscEnableHf32](asc_enable_hf32.md)（`related`）：《AscSetHf32RoundMode》说明设置HF32模式舍入方式。使用该接口前需要先使用asc_enable_hf32开启HF32模式。；《AscEnableHf32》说明设置Mmad计算开启HF32模式，开启后Mmad计算FP32数据性能提升但会带来一定精度损失。。二者在HF32舍入模式只有在HF32/Trans开启后生效，枚举、基础API、Matmul API和关闭FP32模式共同界定状态机上存在可执行的直接衔接。
- [Cube计算(ISASI)HF32](../../basic_api/cube_compute/mmad_compute_key_features/hf32.md)（`related`）：《AscSetHf32RoundMode》说明设置HF32模式舍入方式。使用该接口前需要先使用asc_enable_hf32开启HF32模式。；《Cube计算(ISASI)HF32》说明HF32的核心功能体现为：用户在输入矩阵A、B矩阵都为fp32数据类型的场景下，当配置开启HF32开关后，fp32数据在执行矩阵乘法运算前会被转换并舍入为HF32（half-fp32）格式。这种做法可使Mmad（f322f32）接口的计算性能提升至原来的两倍，但会带来一定的精度损失。需要注意的是，尽管中间计算使用HF32格式，最终的运算结果仍以fp32格式输出，以保证后续处理的兼容性。。二者在HF32舍入模式只有在HF32/Trans开启后生效，枚举、基础API、Matmul API和关闭FP32模式共同界定状态机上存在可执行的直接衔接。
- [SetHF32](../../adv_api/cube_compute/matmul_kernel/set_hf32.md)（`related`）：《AscSetHf32RoundMode》说明设置HF32模式舍入方式。使用该接口前需要先使用asc_enable_hf32开启HF32模式。；《SetHF32》说明在纯Cube模式（只有矩阵计算）下，设置是否开启HF32（矩阵乘计算时可采用的数据类型）模式。开启后，在矩阵乘计算时，float32数据类型会转换为hf32数据类型，可提升计算性能，但同时也会带来精度损失。。二者在HF32舍入模式只有在HF32/Trans开启后生效，枚举、基础API、Matmul API和关闭FP32模式共同界定状态机上存在可执行的直接衔接。
- [SetHF32Mode](../../basic_api/cube_compute/mmad_compute_aux_config/set_hf32_mode.md)（`related`）：《AscSetHf32RoundMode》说明设置HF32模式舍入方式。使用该接口前需要先使用asc_enable_hf32开启HF32模式。；《SetHF32Mode》说明用于设置Mmad计算是否开启HF32模式，开启该模式后L0A Buffer/L0B Buffer中的FP32数据将在参与Mmad计算之前被舍入为HF32。。二者在HF32舍入模式只有在HF32/Trans开启后生效，枚举、基础API、Matmul API和关闭FP32模式共同界定状态机上存在可执行的直接衔接。
- [基础APIHF32](../../basic_api/cube_compute_tensor_api/mmad_compute_key_features/hf32.md)（`related`）：《AscSetHf32RoundMode》说明设置HF32模式舍入方式。使用该接口前需要先使用asc_enable_hf32开启HF32模式。；《基础APIHF32》说明HF32的核心功能体现为：用户在输入矩阵A和B都为fp32数据类型的场景下，当配置开启HF32开关后，fp32数据在执行矩阵乘法运算前会被转换并舍入为HF32（half-fp32）格式。这种做法可使Mmad（fp32->fp32）接口的计算性能提升至原来的两倍，但会带来一定的精度损失。需要注意的是，尽管中间计算使用HF32格式，最终的运算结果仍以fp32格式输出，以保证后续处理的兼容性。。二者在HF32舍入模式只有在HF32/Trans开启后生效，枚举、基础API、Matmul API和关闭FP32模式共同界定状态机上存在可执行的直接衔接。
- [AscEnableHf32Trans](asc_enable_hf32_trans.md)（`same_topic`）：《AscSetHf32RoundMode》说明设置HF32模式舍入方式。使用该接口前需要先使用asc_enable_hf32开启HF32模式。；《AscEnableHf32Trans》说明设置HF32模式舍入方式。使用该接口前需要先使用asc_enable_hf32开启HF32模式。。二者在HF32舍入模式只有在HF32/Trans开启后生效，枚举、基础API、Matmul API和关闭FP32模式共同界定状态机上存在可执行的直接衔接。
- [AscHf32RoundMode](../enum/asc_hf32_round_mode.md)（`same_topic`）：《AscSetHf32RoundMode》说明设置HF32模式舍入方式。使用该接口前需要先使用asc_enable_hf32开启HF32模式。；《AscHf32RoundMode》说明用于Mmad计算开启HF32模式时FP32到HF32的舍入模式管理策略，在调用asc_set_hf32_round_mode时使用。。二者在HF32舍入模式只有在HF32/Trans开启后生效，枚举、基础API、Matmul API和关闭FP32模式共同界定状态机上存在可执行的直接衔接。
- [AscSetFp32Mode](asc_set_fp32_mode.md)（`same_topic`）：AscSetFp32Mode 与《AscSetHf32RoundMode》的实质衔接是：AscSetFp32Mode 与 HF32 round/enable/trans 配置共同决定 AscMmad 的 FP32/HF32 计算模式，Mmad 约束和 HF32 指南说明精度与方向设置。
- [SetHF32TransMode](../../basic_api/cube_compute/mmad_compute_aux_config/set_hf32_trans_mode.md)（`same_topic`）：《AscSetHf32RoundMode》说明设置HF32模式舍入方式。使用该接口前需要先使用asc_enable_hf32开启HF32模式。；《SetHF32TransMode》说明设置HF32模式取整的具体方式，需要先使用SetHF32Mode开启HF32取整模式。。二者在HF32舍入模式只有在HF32/Trans开启后生效，枚举、基础API、Matmul API和关闭FP32模式共同界定状态机上存在可执行的直接衔接。
<!-- cannbot:related:end -->
