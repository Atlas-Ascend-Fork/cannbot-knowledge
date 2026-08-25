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
