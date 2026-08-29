---
type: API
title: AscendcAssert
description: CPU/NPU域断言接口，当断言条件不满足时输出断言信息并格式化打印，主要用于调试阶段。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/exception_detection/ascendc_assert.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# AscendcAssert

CPU/NPU 域断言接口。断言条件不满足时输出断言信息并格式化打印，NPU 模式下还会触发 Trap 中断。参数 condition 为断言条件，format 为格式化字符串。仅调试阶段使用。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [LinalgCholesky A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/math/linalg_cholesky.md)（`related`）：Cholesky 实现规定“Device 仅在每个对角主元/Schur 残差处执行 `ascendc_assert(value>0)`。”；AscendcAssert 页说明“断言条件不满足时输出断言信息并格式化打印，NPU 模式下还会触发 Trap 中断。”，后者给出非正定主元在设备侧的失败传播机制。
- [Assert](assert.md)（`same_topic`）：AscendcAssert 卡说明“断言条件不满足时输出断言信息并格式化打印，NPU 模式下还会触发 Trap 中断。”；Assert 卡说明“条件不为真时输出断言条件并格式化打印，NPU 模式下触发 Trap 中断。”，两者具有相同 CPU/NPU 调试语义、参数角色与 Trap 行为，只是公开符号不同。
<!-- cannbot:related:end -->
