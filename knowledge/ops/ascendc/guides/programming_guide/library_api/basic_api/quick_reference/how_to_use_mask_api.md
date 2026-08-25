---
type: Guide
title: 如何使用掩码操作API
description: Mask用于控制矢量计算中参与计算的元素个数，支持以下工作模式及配置方式：
tags: [task.lookup, topic.implementation.api_layer]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/library_api/basic_api/quick_reference/how_to_use_mask_api.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 如何使用掩码操作API

Mask用于控制矢量计算中参与计算的元素个数，支持以下工作模式及配置方式：
Mask工作模式
Mask配置方式
Mask操作的使用方式如下：
Mask操作的使用方式
典型场景的使用示例如下：
-   场景1：Normal模式 + 外部API配置 + 高维切分计算API
-   场景2：Counter模式 + 外部API配置 + 高维切分计算API
-   场景3：Counter模式 + 外部API配置 + 前n个数据计算接口配合使用
