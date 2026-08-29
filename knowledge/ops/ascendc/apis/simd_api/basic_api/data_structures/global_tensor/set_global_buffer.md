---
type: API
title: SetGlobalBuffer
description: 传入全局数据地址，初始化GlobalTensor。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/SetGlobalBuffer.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetGlobalBuffer

传入 GM 全局数据地址和大小，初始化 GlobalTensor。参数：buffer 为 GlobalTensor 源操作数（GM 地址），bufferSize 为元素个数。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [DataCopy 不自动按 tile 推进须显式元素 offset](../../../../../runbooks/precision/datacopy_setglobalbuffer_no_auto_advance_tileoffset.md)（`exemplifies`）：“传入 GM 全局数据地址和大小，初始化 GlobalTensor。”给出焦点端事实；“GlobalTensor::SetGlobalBuffer(ptr, len)”给出候选端事实。API 卡说明 SetGlobalBuffer 只绑定 GM 地址与大小，runbook 用该调用复现多次 DataCopy 不会自动推进位置的故障，并给出显式 tileOffset 的修复边界。
- [GlobalTensor构造函数](global_tensor_constructor.md)（`related`）：GlobalTensor 默认构造函数，创建空的 GlobalTensor 对象，后续通过 SetGlobalBuffer 设置 GM 地址和大小。模板参数 T 为数据类型。支持 950/a2/a3。；传入 GM 全局数据地址和大小，初始化 GlobalTensor。参数：buffer 为 GlobalTensor 源操作数（GM 地址），bufferSize 为元素个数。支持 950/a2/a3。。构造函数只产生空对象并明确指定后接 SetGlobalBuffer，目标接口负责绑定 GM 地址和元素数，二者组成 GlobalTensor 从空对象到可访问全局内存视图的初始化顺序。
<!-- cannbot:related:end -->
