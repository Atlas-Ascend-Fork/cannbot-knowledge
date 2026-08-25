---
type: API
title: operator=（OpMC2Def）
description: 赋值运算符重载，实现OpMC2Def类对象的深拷贝。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpMC2Def/operator.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# operator=（OpMC2Def）

OpMC2Def类的赋值运算符重载，实现OpMC2Def对象的深拷贝。函数原型：OpMC2Def &operator=(const OpMC2Def &def)。参数：def（输入，被拷贝的OpMC2Def类对象，包含通信域名称等配置信息）。返回值：拷贝后的结果对象的引用，支持链式赋值。无约束。用于在通算融合算子原型注册场景下安全地复制OpMC2Def对象，确保通信域配置信息的独立副本，避免多个算子实例间共享配置导致的冲突。

<!-- cannbot:related:start -->
## 相关

- [OpMC2Def构造函数](op_mc2_def_constructor.md)（`same_topic`）：Operator 将 MC2 定义绑定到具体通信算子语义，是构造后的直接配置。
- [OpMC2Def简介](op_mc2_def_intro.md)（`same_topic`）：OpMC2Def简介 与《operator=（OpMC2Def）》的实质衔接是：OpMC2Def 在 host 原型侧声明 HcclGroup 与 HcclServerType，构造后把通信域映射为核侧 HCCL Context；MC2 OpDef 是其注册入口。
<!-- cannbot:related:end -->
