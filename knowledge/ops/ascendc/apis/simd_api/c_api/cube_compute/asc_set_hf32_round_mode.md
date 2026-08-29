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

- [AscEnableHf32](asc_enable_hf32.md)（`related`）：HF32模式启用后，FP32转换为HF32格式的舍入模式由配套的asc_set_hf32_round_mode接口配置，须在本接口之后调用该配套接口配置舍入模式，否则舍入模式沿用上次配置或默认值。；设置HF32模式舍入方式。使用该接口前需要先使用asc_enable_hf32开启HF32模式。两卡给出相互一致的先启用 HF32、再配置舍入模式的有序调用合同。
- [AscHf32RoundMode](../enum/asc_hf32_round_mode.md)（`related`）：“用于Mmad计算开启HF32模式时FP32到HF32的舍入模式管理策略，在调用asc_set_hf32_round_mode时使用。枚举值：NEAREST_ZERO（FP32以向零靠近的方式四舍五入为HF32）、NEAREST_EVEN（FP32以最接近偶数的方式四舍五入为HF32）。”与“参数：hf32_round_mode(输入): HF32舍入模式控制入参，asc_hf32_round_mode枚举类型，支持如下2种枚举值： &nbsp;&nbsp;&bull; NEAREST_ZE。”分别给出双端正文事实；枚举卡定义 FP32 到 HF32 的两个舍入策略，设置接口把 asc_hf32_round_mode 作为直接入参，连接枚举语义与寄存器配置调用。
<!-- cannbot:related:end -->
