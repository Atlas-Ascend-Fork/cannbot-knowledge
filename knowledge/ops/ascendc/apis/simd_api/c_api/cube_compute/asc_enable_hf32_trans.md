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

- [AscEnableHf32](asc_enable_hf32.md)（`related`）：舍入接口要求“设置HF32模式舍入方式。使用该接口前需要先使用asc_enable_hf32开启HF32模式。”；HF32 开启接口进一步限定“须在本接口之后调用该配套接口配置舍入模式，否则舍入模式沿用上次配置或默认值。”，两端共同确定先启用、后配置舍入的顺序。
<!-- cannbot:related:end -->
