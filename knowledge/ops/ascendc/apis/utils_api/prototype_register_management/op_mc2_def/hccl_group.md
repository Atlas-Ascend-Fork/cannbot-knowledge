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

- [GetHcclContext](../../../simd_api/adv_api/hccl_communication/hccl_context/get_hccl_context.md)（`related`）：获取指定Index通信域的context（消息区）地址。；配置通信域名称，每个名称对应一个通信域。配置后在Kernel侧调用GetHcclContext接口可获取通信域对应的context（消息区）地址。。HcclGroup 在原型侧声明通信域名称，GetHcclContext 在 Kernel 侧按索引取得该域的 context 地址，二者是通算融合通信域从注册到运行时访问的直接链。
- [HCCL Context简介](../../../simd_api/adv_api/hccl_communication/hccl_context/hccl_context_intro.md)（`related`）：“需要同步在host侧调用HcclGroup接口配置通信域名称后”给出焦点端事实；“配置后在Kernel侧调用GetHcclContext接口可获取通信域对应的context（消息区）地址。”给出候选端事实。简介卡要求 Host 先用 HcclGroup 配置通信域名称，HcclGroup 卡明确配置结果供 Kernel 的 GetHcclContext 取址，二者连接 Host 注册与 Device 使用。
- [MC2（OpDef）](../op_def/mc2.md)（`related`）：HcclGroup 规定“使用该接口前，算子需要先通过MC2接口注册该算子是通算融合算子，注册后即返回一个OpMC2Def结构。”；MC2 页说明“调用该接口后会返回一个OpMC2Def结构，后续可通过该结构配置通信域名称。”，构成 MC2 注册到 HcclGroup 配置的强制调用顺序。
<!-- cannbot:related:end -->
