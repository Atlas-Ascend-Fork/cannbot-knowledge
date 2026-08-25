---
type: API
title: EnableBias
description: 设置Bias是否参与运算，设置的信息必须与Kernel侧保持一致。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/EnableBias.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# EnableBias

设置Bias是否参与运算，设置的信息必须与Kernel侧保持一致。

参数：
- isBiasIn（输入）：设置是否有Bias参与运算。 true：有Bias参与运算。 false：无Bias参与运算。

返回值：-1表示设置失败；0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [GetTiling](get_tiling.md)（`related`）：Bias 开关和类型配置由 GetTiling 汇总，生成 Kernel 消费的最终参数。
- [DisableBias](../matmul_kernel/disable_bias.md)（`same_topic`）：DisableBias 与《EnableBias》的实质衔接是：DisableBias、ClearBias、SetBias 和 EnableBias 改变同一 Matmul 对象的 bias 状态，适用于迭代间切换。
- [SetBias](set_bias.md)（`same_topic`）：SetBias 文档明确说明 EnableBias 功能相同且为推荐替代；目标接口是同一 Matmul tiling 开关的当前入口。
- [SetBiasType](set_bias_type.md)（`same_topic`）：SetBiasType 声明 bias 的位置、格式和 dtype，必须与 EnableBias 和 Kernel 实际输入一致。
<!-- cannbot:related:end -->
