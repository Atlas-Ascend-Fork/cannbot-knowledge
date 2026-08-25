---
type: API
title: SetHF32
description: 在纯Cube模式（只有矩阵计算）下，设置是否开启HF32（矩阵乘计算时可采用的数据类型）模式。开启后，在矩阵乘计算时，float32数据类型会转换为hf32数据类型，可提升计算性能，但同时也会带来精度损失。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetHF32.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetHF32

在纯Cube模式（只有矩阵计算）下，设置是否开启HF32（矩阵乘计算时可采用的数据类型）模式。开启后，在矩阵乘计算时，float32数据类型会转换为hf32数据类型，可提升计算性能，但同时也会带来精度损失。

函数原型：__aicore__ inline void SetHF32(bool enableHF32 = false, int32_t transMode = 0)

参数：
- enableHF32（输入）：配置是否开启HF32模式，默认值false(不开启)。
- transMode（输入）：配置在开启HF32模式时，float转换为hf32时所采用的ROUND模式。默认值0。 0：就近舍入，距离相等时向偶数进位。 1：就近舍入，距离相等时向远离0方向进位。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品、Kirin X90、Kirin 9030。

<!-- cannbot:related:start -->
## 相关

- [AscEnableHf32](../../../c_api/cube_compute/asc_enable_hf32.md)（`related`）：AscEnableHf32 与《SetHF32》的实质衔接是：HF32 开关与转置开关、舍入模式和 C/C++ 配置入口共同决定 Cube FP32 的计算模式，特性页解释性能精度权衡。
- [AscSetHf32RoundMode](../../../c_api/cube_compute/asc_set_hf32_round_mode.md)（`related`）：《AscSetHf32RoundMode》说明设置HF32模式舍入方式。使用该接口前需要先使用asc_enable_hf32开启HF32模式。；《SetHF32》说明在纯Cube模式（只有矩阵计算）下，设置是否开启HF32（矩阵乘计算时可采用的数据类型）模式。开启后，在矩阵乘计算时，float32数据类型会转换为hf32数据类型，可提升计算性能，但同时也会带来精度损失。。二者在HF32舍入模式只有在HF32/Trans开启后生效，枚举、基础API、Matmul API和关闭FP32模式共同界定状态机上存在可执行的直接衔接。
- [SetHF32Mode](../../../basic_api/cube_compute/mmad_compute_aux_config/set_hf32_mode.md)（`related`）：基础 MMAD 的 SetHF32Mode 与 Matmul 高阶 SetHF32 都控制 fp32→HF32 性能/精度取舍，但作用接口层不同。
- [SetHF32TransMode](../../../basic_api/cube_compute/mmad_compute_aux_config/set_hf32_trans_mode.md)（`related`）：Matmul 高阶 API 的 SetHF32 将底层 HF32 配置接入矩阵乘对象，连接基础辅助配置与高阶调用。
- [AscHf32RoundMode](../../../c_api/enum/asc_hf32_round_mode.md)（`same_topic`）：《AscHf32RoundMode》处理“用于Mmad计算开启HF32模式时FP32到HF32的舍入模式管理策略，在调用asc_set_hf32_round_mode时使用。”。《SetHF32》明确“在纯Cube模式（只有矩阵计算）下，设置是否开启HF32（矩阵乘计算时可采用的数据类型）模式。开启后，在矩阵乘计算时，float32数据类型会转换为hf32数据类型，可提升计算性能，但同时也会带来精度损失。”，可直接用于核对HF32 rounding/trans mode 的配置入口及其对 Mmad 执行精度的直接影响。
<!-- cannbot:related:end -->
