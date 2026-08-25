---
type: API
title: HCCL Context简介
description: 本章节的接口用于在kernel侧设置/获取通算融合算子每个通信域对应的context（消息区）地址。需要同步在host侧调用HcclGroup接口配置通信域名称后，才可以调用GetHcclContext获取对应的context地址。
tags: [task.lookup, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL-Context/HCCL_Context_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# HCCL Context简介

本章节的接口用于在kernel侧设置 获取通算融合算子每个通信域对应的context（消息区）地址。需要同步在host侧调用HcclGroup接口配置通信域名称后，才可以调用GetHcclContext获取对应的context地址。

<!-- cannbot:related:start -->
## 相关

- [HCCL Kernel侧接口](../hccl_kernel/hccl_kernel.md)（`related`）：HCCL Context简介 与《HCCL Kernel侧接口》的实质衔接是：HCCL context 需要 host HcclGroup 先声明通信域，再由 kernel Get/SetHcclContext 使用；通信类、kernel/tiling 与使用说明共同闭合地址配置到集合通信执行。
- [HCCL Tiling侧接口](../hccl_tiling/hccl_tiling.md)（`related`）：HCCL Context简介 与《HCCL Tiling侧接口》的实质衔接是：HCCL context 需要 host HcclGroup 先声明通信域，再由 kernel Get/SetHcclContext 使用；通信类、kernel/tiling 与使用说明共同闭合地址配置到集合通信执行。
- [HCCL使用说明](../hccl_kernel/hccl_usage.md)（`related`）：HCCL Context简介 与《HCCL使用说明》的实质衔接是：HCCL context 需要 host HcclGroup 先声明通信域，再由 kernel Get/SetHcclContext 使用；通信类、kernel/tiling 与使用说明共同闭合地址配置到集合通信执行。
- [HCCL通信类](../hccl_communication.md)（`related`）：HCCL Context简介 与《HCCL通信类》的实质衔接是：HCCL context 需要 host HcclGroup 先声明通信域，再由 kernel Get/SetHcclContext 使用；通信类、kernel/tiling 与使用说明共同闭合地址配置到集合通信执行。
- [HcclGroup（OpMC2Def）](../../../../utils_api/prototype_register_management/op_mc2_def/hccl_group.md)（`related`）：HCCL Context简介 与《HcclGroup（OpMC2Def）》的实质衔接是：HCCL context 需要 host HcclGroup 先声明通信域，再由 kernel Get/SetHcclContext 使用；通信类、kernel/tiling 与使用说明共同闭合地址配置到集合通信执行。
- [GetHcclContext](get_hccl_context.md)（`same_topic`）：HCCL Context简介 与《GetHcclContext》的实质衔接是：HCCL context 需要 host HcclGroup 先声明通信域，再由 kernel Get/SetHcclContext 使用；通信类、kernel/tiling 与使用说明共同闭合地址配置到集合通信执行。
- [HCCL Context](hccl_context.md)（`same_topic`）：HCCL Context简介 与《HCCL Context》的实质衔接是：HCCL context 需要 host HcclGroup 先声明通信域，再由 kernel Get/SetHcclContext 使用；通信类、kernel/tiling 与使用说明共同闭合地址配置到集合通信执行。
- [OpMC2Def简介](../../../../utils_api/prototype_register_management/op_mc2_def/op_mc2_def_intro.md)（`same_topic`）：OpMC2Def简介 与《HCCL Context简介》的实质衔接是：OpMC2Def 在 host 原型侧声明 HcclGroup 与 HcclServerType，构造后把通信域映射为核侧 HCCL Context；MC2 OpDef 是其注册入口。
- [SetHcclContext](set_hccl_context.md)（`same_topic`）：HCCL Context简介 与《SetHcclContext》的实质衔接是：HCCL context 需要 host HcclGroup 先声明通信域，再由 kernel Get/SetHcclContext 使用；通信类、kernel/tiling 与使用说明共同闭合地址配置到集合通信执行。
<!-- cannbot:related:end -->
