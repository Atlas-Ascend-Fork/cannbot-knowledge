---
type: API
title: Mmad计算辅助配置接口
description: Mmad计算辅助配置接口列表如下：
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/mmad_compute_aux_config/mmad_compute_aux_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Mmad计算辅助配置接口

提供 Mmad 矩阵乘计算的辅助配置接口，用于设置计算模式与精度控制。
包含 SetMMColumnMajor/SetMMRowMajor 设置矩阵主序方向，SetHF32Mode 启用或关闭 HF32 半精度浮点模式，SetHF32TransMode 设置 HF32 转置模式。
这些接口在 Mmad 计算前调用，影响后续矩阵乘的数据排布与计算精度。

<!-- cannbot:related:start -->
## 相关

- [Mmad](../mmad_compute/mmad.md)（`related`）：辅助配置页规定“这些接口在 Mmad 计算前调用，影响后续矩阵乘的数据排布与计算精度。”；Mmad 页说明“完成L0A Buffer上左矩阵A和L0B Buffer上右矩阵B的矩阵乘加，结果写入L0C Buffer上结果矩阵C。”，前者配置主序和 HF32 状态，后者是直接消费这些状态的计算。
- [基础APIHF32](../mmad_compute_key_features/hf32.md)（`related`）：辅助配置页说明“SetHF32Mode 启用或关闭 HF32 半精度浮点模式”；HF32 页说明“通过Mmad接口的模板参数配置HF32模式。”，两端分别给出 HF32 的运行配置入口和 Mmad 精度模式效果。
<!-- cannbot:related:end -->
