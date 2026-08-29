---
type: API
title: Init
description: 用于内存和同步流水事件EventID的初始化。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/Init.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# Init

头文件路径为："basic_api/kernel_tpipe.h"。

用于内存和同步流水事件EventID的初始化。

约束：-   Tpipe对象复用时，要与Destroy接口成对使用，每次复用需要先Destroy释放资源，再调用init重新初始化。
-   Tpipe构造函数内部已调用Init，无需在Tpipe对象初始化后再额外调用。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [Destroy](destroy.md)（`related`）：Tpipe对象复用时，要与Destroy接口成对使用，每次复用需要先Destroy释放资源，再调用init重新初始化。；约束：用于重复申请释放tpipe，创建tpipe对象后，可调用Destroy手动释放资源。。Init 明确规定复用前先 Destroy，Destroy 则提供手工释放资源的对应动作，两者共同定义 TPipe 重复申请释放的生命周期。
- [Reset](reset.md)（`related`）：完成资源的释放与eventId等变量的初始化操作，恢复到TPipe的初始化状态。；用于内存和同步流水事件EventID的初始化。；Reset 释放当前资源并恢复 Init 建立的内存与 EventID 状态，两接口构成 TPipe 资源生命周期。
<!-- cannbot:related:end -->
