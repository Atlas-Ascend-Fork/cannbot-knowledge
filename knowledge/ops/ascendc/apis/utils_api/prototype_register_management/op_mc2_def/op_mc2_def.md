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

- [MC²算子性能调优案例](../../../../guides/operator_practice/best_practices/mc_operator_tuning.md)（`explains`）：《MC²算子性能调优案例》的任务是“MC2通算融合算子性能调优案例，通过数据切分实现计算与通信流水掩盖，介绍切分策略制定与优化方法。”。《OpMC2Def》具体提供“OpMC2Def算子定义接口索引。”，它直接用于MC2 通算融合的 Matmul 性能入口和 MC2 原型配置。
- [HcclGroup（OpMC2Def）](hccl_group.md)（`same_topic`）：OpMC2Def 类型承载 HcclGroup 等 MC2 注册字段，是该 setter 的所属核心对象。
- [HcclServerType](hccl_server_type.md)（`same_topic`）：HcclServerType 与《OpMC2Def》的实质衔接是：HcclServerType 是 OpMC2Def 注册中的 server 枚举；构造、HcclGroup 和 MC2 OpDef 共同决定 MC2 原型如何声明通信域与服务端角色。
- [MC2（OpDef）](../op_def/mc2.md)（`same_topic`）：MC2 返回 OpMC2Def，后续通信域配置都在该对象上完成。
- [OpMC2Def构造函数](op_mc2_def_constructor.md)（`same_topic`）：构造函数创建 OpMC2Def 对象，类型页定义其注册字段和链式配置。
- [OpMC2Def简介](op_mc2_def_intro.md)（`same_topic`）：OpMC2Def简介 与《OpMC2Def》的实质衔接是：OpMC2Def 在 host 原型侧声明 HcclGroup 与 HcclServerType，构造后把通信域映射为核侧 HCCL Context；MC2 OpDef 是其注册入口。
<!-- cannbot:related:end -->
