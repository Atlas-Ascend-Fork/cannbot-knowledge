---
type: API
title: 算法
description: 提供max和min算法函数接口。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/algorithms/algorithms.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 算法

提供标量比较算法接口，包含 max 和 min 两个函数模板。两者均比较两个相同数据类型的输入并返回较大值或较小值，支持 bool、int8_t、uint8_t、int16_t、uint16_t、int32_t、uint32_t、float、int64_t、uint64_t 等整型与浮点类型。
约束：两个源操作数的数据类型必须相同；U 模板参数当前为预留，必须与 T 保持一致。可在 Host 侧与 AI Core 侧使用。
