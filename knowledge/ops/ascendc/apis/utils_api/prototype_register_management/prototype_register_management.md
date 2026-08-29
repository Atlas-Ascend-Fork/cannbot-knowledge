---
type: API
title: 原型注册与管理
description: 算子原型注册与管理接口索引。
tags: [task.lookup, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/prototype_register_management.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 原型注册与管理

算子原型注册与管理接口的总入口，包含注册宏（OP_ADD、REGISTER_OP_AICORE_CONFIG）和算子定义类（OpDef、OpParamDef、OpAttrDef）。通过 OpAICoreDef、OpAICPUDef、OpHostCPUDef 分别定义不同执行引擎的行为，OpAICoreConfig 配置编译选项，OpMC2Def 支持多机通信场景。这些接口共同构成 Ascend C 算子注册的完整框架。
