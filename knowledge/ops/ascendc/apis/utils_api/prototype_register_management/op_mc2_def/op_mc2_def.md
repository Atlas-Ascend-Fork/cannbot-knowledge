---
type: API
title: OpMC2Def
description: OpMC2Def算子定义接口索引。
tags: [task.lookup, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpMC2Def/OpMC2Def.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# OpMC2Def

OpMC2Def 用于定义算子在 MC2（多机多卡通信）场景下的执行属性，包括 HCCL 通信组配置（HcclGroup）和服务器类型（HcclServerType）。通过构造函数初始化并支持赋值操作，用于涉及跨节点集合通信的算子注册。
