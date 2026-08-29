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

- [GetHcclContext](get_hccl_context.md)（`related`）：“才可以调用GetHcclContext获取对应的context地址。”给出焦点端事实；“获取指定Index通信域的context（消息区）地址。”给出候选端事实。简介卡给出调用 GetHcclContext 前必须完成通信域配置的先决条件，接口卡定义按 Index 取得消息区地址的结果，构成明确的配置后取址链。
- [HcclGroup（OpMC2Def）](../../../../utils_api/prototype_register_management/op_mc2_def/hccl_group.md)（`related`）：“需要同步在host侧调用HcclGroup接口配置通信域名称后”给出焦点端事实；“配置后在Kernel侧调用GetHcclContext接口可获取通信域对应的context（消息区）地址。”给出候选端事实。简介卡要求 Host 先用 HcclGroup 配置通信域名称，HcclGroup 卡明确配置结果供 Kernel 的 GetHcclContext 取址，二者连接 Host 注册与 Device 使用。
- [OpMC2Def](../../../../utils_api/prototype_register_management/op_mc2_def/op_mc2_def.md)（`related`）：“用于涉及跨节点集合通信的算子注册”给出 MC2 注册场景，“需要同步在host侧调用HcclGroup接口配置通信域名称后，才可以调用GetHcclContext获取对应的context地址”把该注册配置连接到 Device 获取通信 context 的前置条件。
<!-- cannbot:related:end -->
