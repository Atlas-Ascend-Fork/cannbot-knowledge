---
type: Guide
title: SGLang Diffusion Helios：NPU调度器sigma转FP32
description: 说明Helios/UniPC为避免Expm1 float64而将sigma转FP32的NPU分支及长去噪数值验收，保留DMD流程差异。
tags:
- task.implementation
- topic.diffusion
- topic.precision
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/models/schedulers/scheduling_helios.py
  role: primary
created_at: '2026-11-08T12:27:29Z'
updated_at: '2026-11-09T04:32:54Z'
platforms: []
---

# SGLang Diffusion Helios：NPU调度器sigma转FP32

## 触发与数值路径

Helios调度器由NumPy构造的sigma默认可能为float64，NPU的Expm1不支持DT_DOUBLE，因此为 UniPC step 的 expm1 将 NPU sigma 转FP32；其他平台保留原路径。step_dmd 不调用 Expm1，convert_flow_pred_to_x0 还会把 sigmas 等转为double，不能将这项适配概括为 DMD 全程FP32。改变的是计算精度，不是删去时间步历史、DMD调整或调度公式。直接全局set_default_dtype会影响权重与其他算子，不是此实现的做法。

接入时核对时间步/sigma设备和dtype，覆盖起终点、不同步数与DMD选项，检查NaN/Inf、单步更新及完整输出质量；FP32可产生累计舍入，不能只验首步。若出现偏差先对照同调度配置的高精度参考并定位敏感步骤，不把异常归因于attention后端。

本卡仅说明模型调度器适配，未运行采样或统计误差，也不承诺所有NPU型号均已验证。
