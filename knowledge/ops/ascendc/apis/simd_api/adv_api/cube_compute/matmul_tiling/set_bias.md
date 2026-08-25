---
type: API
title: SetBias
description: EnableBias接口功能与该接口相同，建议使用EnableBias。 设置Bias是否参与运算。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetBias.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetBias

EnableBias接口功能与该接口相同，建议使用EnableBias。 设置Bias是否参与运算。

参数：
- isBiasIn（输入）：设置是否有Bias参与运算

返回值：-1表示设置失败； 0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [EnableBias](enable_bias.md)（`same_topic`）：SetBias 文档明确说明 EnableBias 功能相同且为推荐替代；目标接口是同一 Matmul tiling 开关的当前入口。
- [SetBias](../matmul_kernel/set_bias.md)（`same_topic`）：焦点处理Matmul SetBias 的启用/禁用状态、Tiling 类型一致性与调用时机；SetBias正文说明“EnableBias接口功能与该接口相同，建议使用EnableBias。 设置Bias是否参与运算”。候选决定 Bias 是否参与、Host/Kernel 类型是否一致，或界定 SetBias 必须发生在迭代前。
<!-- cannbot:related:end -->
