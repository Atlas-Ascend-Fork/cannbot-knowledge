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

<!-- cannbot:related:start -->
## 相关

- [HCCL Context简介](../../../simd_api/adv_api/hccl_communication/hccl_context/hccl_context_intro.md)（`related`）：“用于涉及跨节点集合通信的算子注册”给出 MC2 注册场景，“需要同步在host侧调用HcclGroup接口配置通信域名称后，才可以调用GetHcclContext获取对应的context地址”把该注册配置连接到 Device 获取通信 context 的前置条件。
- [MC2（OpDef）](../op_def/mc2.md)（`same_topic`）：“OpMC2Def 用于定义算子在 MC2（多机多卡通信）场景下的执行属性”说明结构体职责，“注册该算子是通算融合算子，调用该接口后会返回一个OpMC2Def结构”说明从 OpDef 进入该结构的注册入口。
<!-- cannbot:related:end -->
