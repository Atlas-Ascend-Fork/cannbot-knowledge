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

<!-- cannbot:related:start -->
## 相关

- [HcclGroup（OpMC2Def）](hccl_group.md)（`same_topic`）：构造函数创建可继续配置 HcclGroup/HcclServerType 的 MC2 定义。
- [HcclServerType](hccl_server_type.md)（`same_topic`）：HcclServerType 与《OpMC2Def构造函数》的实质衔接是：HcclServerType 是 OpMC2Def 注册中的 server 枚举；构造、HcclGroup 和 MC2 OpDef 共同决定 MC2 原型如何声明通信域与服务端角色。
- [MC2（OpDef）](../op_def/mc2.md)（`same_topic`）：OpDef::MC2 创建并挂接该对象，连接普通 OpDef 与 MC2 扩展定义。
- [OpMC2Def](op_mc2_def.md)（`same_topic`）：构造函数创建 OpMC2Def 对象，类型页定义其注册字段和链式配置。
- [OpMC2Def简介](op_mc2_def_intro.md)（`same_topic`）：OpMC2Def简介 与《OpMC2Def构造函数》的实质衔接是：OpMC2Def 在 host 原型侧声明 HcclGroup 与 HcclServerType，构造后把通信域映射为核侧 HCCL Context；MC2 OpDef 是其注册入口。
- [operator=（OpMC2Def）](operator.md)（`same_topic`）：Operator 将 MC2 定义绑定到具体通信算子语义，是构造后的直接配置。
<!-- cannbot:related:end -->
