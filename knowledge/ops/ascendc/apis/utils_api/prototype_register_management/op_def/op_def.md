---
type: API
title: OpDef
description: OpDef算子定义接口索引。
tags: [task.lookup, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpDef/OpDef.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# OpDef

OpDef 是算子原型定义的核心类，用于声明算子的输入（Input）、输出（Output）、属性（Attr）以及 Shape 与数据类型推导函数（SetInferShape、SetInferShapeRange、SetInferDataType）。通过 AICore、AICPU、HostCPU、MC2 子配置指定算子的执行引擎，并支持 Fallback 机制（EnableFallBack）、格式匹配模式（FormatMatchMode）和注释（Comment）。
