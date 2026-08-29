---
type: API
title: OpAICoreDef
description: OpAICoreDef算子定义接口索引。
tags: [task.lookup, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICoreDef/OpAICoreDef.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# OpAICoreDef

OpAICoreDef 用于定义算子在 AICore 上的行为，包括 Tiling 设置（SetTiling）、支持性检查（SetCheckSupport）、格式选择（SetOpSelectFormat）、支持信息（SetOpSupportInfo）、规格信息（SetOpSpecInfo）和参数泛化（SetParamGeneralize）。还提供 AddConfig 添加多档配置和 LaunchWithZeroEleOutputTensors 控制零元素输出的启动行为。
