---
type: API
title: OpMC2Def简介
description: 该类用于在host侧配置通算融合算子的通信域名称。配置后在kernel侧可以获取通信域对应的context（消息区）地址。
tags: [task.lookup, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpMC2Def/OpMC2Def_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# OpMC2Def简介

OpMC2Def类用于在Host侧配置通算融合算子的通信域名称，是通算融合算子原型注册管理的重要组成部分。配置完成后，在Kernel侧可以获取通信域对应的context（消息区）地址，从而支持通算融合场景下的集合通信操作。该类与OpParamDef（算子参数定义）、OpAttrDef（算子属性定义）等类配合使用，完成通算融合算子原型的完整定义。通算融合是将计算与通信融合执行的技术。
