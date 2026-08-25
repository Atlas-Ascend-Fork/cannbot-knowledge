---
type: API
title: TBufPool
description: TBufPool对象构造函数，初始化数据成员，支持指定逻辑位置和可分配Buffer数量。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TBufPool/TBufPool_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# TBufPool

头文件路径为："basic_api/kernel_tpipe.h"。

创建TBufPool对象时，初始化数据成员。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [自定义TBufPool](../custom_t_buf_pool/custom_t_buf_pool.md)（`related`）：CustomTBufPool 仅在需要外部地址/手动布局时替代普通池。
- [InitBufPool](init_buf_pool.md)（`same_topic`）：构造后需 InitBufPool 绑定物理范围才可分配。
- [InitBuffer](init_buffer.md)（`same_topic`）：构造池对象后必须 InitBufPool/InitBuffer 才有可用容量。
- [TBufPool](t_buf_pool.md)（`same_topic`）：类型页定义构造函数产生的池对象和容量成员。
<!-- cannbot:related:end -->
