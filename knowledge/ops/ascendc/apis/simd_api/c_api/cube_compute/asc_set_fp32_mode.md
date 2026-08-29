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

- [AscEnableHf32](asc_enable_hf32.md)（`same_topic`）：如需开启HF32模式，请重新调用asc_enable_hf32接口。；如需关闭HF32模式，请重新调用asc_set_fp32_mode接口。。两个配置接口在正文中互相声明为 FP32/HF32 模式切换的反向操作，共同决定后续 asc_mmad 的输入舍入状态。
<!-- cannbot:related:end -->
