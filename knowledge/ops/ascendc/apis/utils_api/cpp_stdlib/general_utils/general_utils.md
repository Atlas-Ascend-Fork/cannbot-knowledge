---
type: API
title: 通用工具
description: 提供integer_sequence等通用工具接口。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/general_utils/general_utils.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 通用工具

提供模板元编程辅助工具，当前包含 integer_sequence。index_sequence 是类模板，用于表示编译时的整数序列；make_index_sequence 是别名模板，用于生成从 0 到 N-1 的整数序列。
约束：N 的范围为 [0, 64]，序列长度最大为 64。适用于需要在编译期展开参数包或遍历索引的模板元编程场景。

<!-- cannbot:related:start -->
## 相关

- [Utils API（库API）](../../../../guides/programming_guide/library_api/utils_api.md)（`explains`）：焦点处理通用工具在 Utils API 导航中的开发入口；Utils API（库API）正文界定“Ascend C开发提供了丰富的通用工具类，涵盖标准库、平台信息获取、上下文构建、运行时编译及日志输出等功能，支持开发者高效实现算子开发与性能优化”。候选指南说明这组通用工具在库 API 中的实际使用位置；成员导航由 part_of 覆盖，不重复连边。
<!-- cannbot:related:end -->
