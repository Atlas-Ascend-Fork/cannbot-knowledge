---
type: API
title: Assert
description: CPU/NPU域assert断言接口，条件判断不为真时输出断言条件并格式化打印，主要用于调试阶段。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/exception_detection/assert.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Assert

CPU/NPU 域 assert 断言接口。条件不为真时输出断言条件并格式化打印，NPU 模式下触发 Trap 中断。参数 condition 为判断条件，format 为格式化字符串。仅调试阶段使用。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [AscendcAssert](ascendc_assert.md)（`same_topic`）：AscendcAssert 卡说明“断言条件不满足时输出断言信息并格式化打印，NPU 模式下还会触发 Trap 中断。”；Assert 卡说明“条件不为真时输出断言条件并格式化打印，NPU 模式下触发 Trap 中断。”，两者具有相同 CPU/NPU 调试语义、参数角色与 Trap 行为，只是公开符号不同。
<!-- cannbot:related:end -->
