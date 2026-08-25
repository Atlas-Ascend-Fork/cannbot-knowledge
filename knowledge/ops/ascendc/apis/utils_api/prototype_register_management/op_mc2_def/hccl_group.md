---
type: API
title: HcclGroup（OpMC2Def）
description: 配置通信域名称，每个名称对应一个通信域。配置后在Kernel侧调用GetHcclContext接口可获取通信域对应的context（消息区）地址。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpMC2Def/HcclGroup.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# HcclGroup

## 功能说明
配置通信域名称，每个名称对应一个通信域。配置后在Kernel侧调用GetHcclContext接口可获取通信域对应的context（消息区）地址。
## 函数原型
## 参数说明
## 约束说明
使用该接口前，算子需要先通过MC2接口注册该算子是通算融合算子，注册后即返回一个OpMC2Def结构。
通信域名称必须先配置为REQUIRED String类型的属性，属性名即为通信域名称。

<!-- cannbot:related:start -->
## 相关

- [GetHcclContext](../../../simd_api/adv_api/hccl_communication/hccl_context/get_hccl_context.md)（`related`）：Kernel 根据组配置取得 HCCL context；组名错误会在这一消费端暴露。
- [HCCL Context简介](../../../simd_api/adv_api/hccl_communication/hccl_context/hccl_context_intro.md)（`related`）：HCCL Context简介 与《HcclGroup（OpMC2Def）》的实质衔接是：HCCL context 需要 host HcclGroup 先声明通信域，再由 kernel Get/SetHcclContext 使用；通信类、kernel/tiling 与使用说明共同闭合地址配置到集合通信执行。
- [SetGroupName](../../../simd_api/adv_api/hccl_communication/hccl_tiling/set_group_name.md)（`related`）：原型侧 HcclGroup 与运行时 tiling 的 SetGroupName 必须指向一致通信组，才能取得正确 context。
- [HcclServerType](hccl_server_type.md)（`same_topic`）：HcclServerType 与《HcclGroup（OpMC2Def）》的实质衔接是：HcclServerType 是 OpMC2Def 注册中的 server 枚举；构造、HcclGroup 和 MC2 OpDef 共同决定 MC2 原型如何声明通信域与服务端角色。
- [MC2（OpDef）](../op_def/mc2.md)（`same_topic`）：HcclGroup 是 MC2 返回对象上的直接后续配置，用于绑定通算融合的通信域名称。
- [OpMC2Def](op_mc2_def.md)（`same_topic`）：OpMC2Def 类型承载 HcclGroup 等 MC2 注册字段，是该 setter 的所属核心对象。
- [OpMC2Def构造函数](op_mc2_def_constructor.md)（`same_topic`）：构造函数创建可继续配置 HcclGroup/HcclServerType 的 MC2 定义。
- [OpMC2Def简介](op_mc2_def_intro.md)（`same_topic`）：OpMC2Def简介 与《HcclGroup（OpMC2Def）》的实质衔接是：OpMC2Def 在 host 原型侧声明 HcclGroup 与 HcclServerType，构造后把通信域映射为核侧 HCCL Context；MC2 OpDef 是其注册入口。
<!-- cannbot:related:end -->
