---
type: API
title: OpMC2Def构造函数
description: 创建OpMC2Def对象时，初始化数据成员。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpMC2Def/OpMC2Def_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# OpMC2Def构造函数

创建OpMC2Def对象时初始化数据成员。函数原型：OpMC2Def()（默认构造）和OpMC2Def(const OpMC2Def &mc2_def)（拷贝构造）。参数：mc2_def（输入，已有的OpMC2Def类对象，用于拷贝构造）。无返回值和约束。OpMC2Def用于在Host侧配置通算融合算子的通信域名称，配置后可在Kernel侧获取通信域对应的context（消息区）地址。
