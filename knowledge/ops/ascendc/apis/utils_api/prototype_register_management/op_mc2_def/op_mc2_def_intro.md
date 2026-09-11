---
type: API
title: OpMC2Def简介
description: 该类用于在host侧配置通算融合算子的通信域名称。配置后在kernel侧可以获取通信域对应的context（消息区）地址。
tags:
- task.lookup
- topic.implementation.operator_registration
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpMC2Def/OpMC2Def_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
---

# OpMC2Def简介<a name="ZH-CN_TOPIC_0000002078492740"></a>

该类用于在host侧配置通算融合算子的通信域名称。配置后在kernel侧可以获取通信域对应的context（消息区）地址。



<!-- cannbot:related:start -->
## 相关

- [HcclServerType](hccl_server_type.md)（`related`）：“使用该接口前，算子需要先通过MC2接口注册该算子是通算融合算子，注册后即返回一个OpMC2Def结构。”与“OpMC2Def类用于在Host侧配置通算融合算子的通信域名称，是通算融合算子原型注册管理的重要组成部分。”分别来自双方当前正文。HcclServerType 明确要求先取得 OpMC2Def，概览卡解释该对象负责 Host 侧通信域配置，因此两卡连接 MC2 注册结果与服务端类型配置步骤。
<!-- cannbot:related:end -->
