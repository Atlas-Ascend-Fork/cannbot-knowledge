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

- [Destroy](destroy.md)（`related`）：TPipe Init 建立资源状态，Destroy 释放同一对象的资源；重复复用 TPipe 时二者构成明确的初始化/清理生命周期。
- [GetBaseAddr](get_base_addr.md)（`related`）：GetBaseAddr 只能在初始化后的逻辑内存池上查询。
- [Reset](reset.md)（`related`）：Reset 释放资源并恢复 eventId 等初始化状态；Init 定义该初始状态及缓冲配置，因此两者构成 TPipe 重新配置前的直接状态转换。
- [TPipe](t_pipe_constructor.md)（`related`）：TPipe 构造函数已经完成默认初始化；Init 卡说明额外 Init 的重置语义，二者共同防止构造后无条件再次初始化。
<!-- cannbot:related:end -->
