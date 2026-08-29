---
type: API
title: AscHf32RoundMode
description: 用于Mmad计算开启HF32模式时FP32到HF32的舍入模式管理策略，在调用asc_set_hf32_round_mode时使用。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/enum/asc_hf32_round_mode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# AscHf32RoundMode

用于Mmad计算开启HF32模式时FP32到HF32的舍入模式管理策略，在调用asc_set_hf32_round_mode时使用。枚举值：NEAREST_ZERO（FP32以向零靠近的方式四舍五入为HF32）、NEAREST_EVEN（FP32以最接近偶数的方式四舍五入为HF32）。HF32模式通过截断FP32尾数位实现更高的矩阵计算吞吐，开发者需根据精度需求选择舍入策略。

<!-- cannbot:related:start -->
## 相关

- [AscSetHf32RoundMode](../cube_compute/asc_set_hf32_round_mode.md)（`related`）：“用于Mmad计算开启HF32模式时FP32到HF32的舍入模式管理策略，在调用asc_set_hf32_round_mode时使用。枚举值：NEAREST_ZERO（FP32以向零靠近的方式四舍五入为HF32）、NEAREST_EVEN（FP32以最接近偶数的方式四舍五入为HF32）。”与“参数：hf32_round_mode(输入): HF32舍入模式控制入参，asc_hf32_round_mode枚举类型，支持如下2种枚举值： &nbsp;&nbsp;&bull; NEAREST_ZE。”分别给出双端正文事实；枚举卡定义 FP32 到 HF32 的两个舍入策略，设置接口把 asc_hf32_round_mode 作为直接入参，连接枚举语义与寄存器配置调用。
<!-- cannbot:related:end -->
