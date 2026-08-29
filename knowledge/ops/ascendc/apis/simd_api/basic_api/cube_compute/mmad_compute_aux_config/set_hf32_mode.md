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

- [Cube计算(ISASI)HF32](../mmad_compute_key_features/hf32.md)（`related`）：HF32 特性卡说明“通过 SetHF32Mode 开启，舍入模式通过 SetHF32TransMode 配置（NEAREST_ZERO 或 NEAREST_EVEN）。”；SetHF32Mode 卡规定“设置 Mmad 计算是否开启 HF32 模式。开启后 L0A Buffer/L0B Buffer 中的 FP32 数据将在参与 Mmad 计算前被舍入为 HF32（half-fp32），可使 f322f32 计算性能提升 2 倍，但有精度损失。”，形成使能开关及其性能/精度后果的直接调用链。
- [SetHF32TransMode](set_hf32_trans_mode.md)（`related`）：设置 Mmad 计算是否开启 HF32 模式。开启后 L0A Buffer/L0B Buffer 中的 FP32 数据将在参与 Mmad 计算前被舍入为 HF32（half-fp32），可使 f322f32 计算性能提升 2 倍，但有精度损失。；设置 HF32 模式下 FP32 到 HF32 的取整方式。须先调用 SetHF32Mode 开启 HF32 模式。。SetHF32Mode 负责启用 Mmad 的 HF32 舍入路径，SetHF32TransMode 依赖前者并配置该路径采用的具体取整规则。
<!-- cannbot:related:end -->
