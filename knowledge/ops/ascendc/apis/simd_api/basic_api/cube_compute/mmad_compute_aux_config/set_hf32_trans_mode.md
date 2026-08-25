---
type: API
title: SetHF32TransMode
description: 设置HF32模式取整的具体方式，需要先使用SetHF32Mode开启HF32取整模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute_aux_config/SetHF32TransMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetHF32TransMode

设置 HF32 模式下 FP32 到 HF32 的取整方式。须先调用 SetHF32Mode 开启 HF32 模式。

参数：mode 为 HF32TransMode 枚举，NEAREST_ZERO 向零靠近四舍五入、NEAREST_EVEN 最接近偶数四舍五入。支持 950/a2/a3/Atlas 200I/500 A2，不支持 Atlas 推理/训练系列。

<!-- cannbot:related:start -->
## 相关

- [AscEnableHf32](../../../c_api/cube_compute/asc_enable_hf32.md)（`related`）：AscEnableHf32 与《SetHF32TransMode》的实质衔接是：HF32 开关与转置开关、舍入模式和 C/C++ 配置入口共同决定 Cube FP32 的计算模式，特性页解释性能精度权衡。
- [Cube计算(ISASI)HF32](../mmad_compute_key_features/hf32.md)（`related`）：HF32 特性要通过 SetHF32TransMode 配置转换行为，连接概念与实际调用。
- [K方向对齐约束](../mmad_compute_key_features/k_direction_alignment_constraint.md)（`related`）：K方向对齐约束 与《SetHF32TransMode》的实质衔接是：K 对齐由 Mmad 的输入格式、数据搬运与参数配置共同决定；普通、Tensor API 和稀疏 Mmad 均需按该约束选择 K 长度及转换模式。
- [SetHF32](../../../adv_api/cube_compute/matmul_kernel/set_hf32.md)（`related`）：Matmul 高阶 API 的 SetHF32 将底层 HF32 配置接入矩阵乘对象，连接基础辅助配置与高阶调用。
- [SetHF32Mode](set_hf32_mode.md)（`related`）：SetHF32Mode 控制 HF32 计算开关，SetHF32TransMode 控制转换模式；二者共同决定 fp32 到 HF32 的 Mmad 行为。
- [AscEnableHf32Trans](../../../c_api/cube_compute/asc_enable_hf32_trans.md)（`same_topic`）：AscEnableHf32Trans 与《SetHF32TransMode》的实质衔接是：AscEnableHf32Trans 只能在启用 HF32 后设置舍入；C++ 对应配置、round mode 枚举和 HF32 指南共同决定 Cube FP32 的精度模式。
- [AscHf32RoundMode](../../../c_api/enum/asc_hf32_round_mode.md)（`same_topic`）：《AscHf32RoundMode》处理“用于Mmad计算开启HF32模式时FP32到HF32的舍入模式管理策略，在调用asc_set_hf32_round_mode时使用。”。《SetHF32TransMode》明确“设置HF32模式取整的具体方式，需要先使用SetHF32Mode开启HF32取整模式。”，可直接用于核对HF32 rounding/trans mode 的配置入口及其对 Mmad 执行精度的直接影响。
- [AscSetHf32RoundMode](../../../c_api/cube_compute/asc_set_hf32_round_mode.md)（`same_topic`）：《AscSetHf32RoundMode》说明设置HF32模式舍入方式。使用该接口前需要先使用asc_enable_hf32开启HF32模式。；《SetHF32TransMode》说明设置HF32模式取整的具体方式，需要先使用SetHF32Mode开启HF32取整模式。。二者在HF32舍入模式只有在HF32/Trans开启后生效，枚举、基础API、Matmul API和关闭FP32模式共同界定状态机上存在可执行的直接衔接。
<!-- cannbot:related:end -->
