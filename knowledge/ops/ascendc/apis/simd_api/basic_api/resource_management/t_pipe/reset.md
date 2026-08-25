---
type: API
title: Reset
description: 完成资源的释放与eventId等变量的初始化操作，恢复到TPipe的初始化状态。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/Reset.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# Reset

头文件路径为："basic_api/kernel_tpipe.h"。

完成资源的释放与eventId等变量的初始化操作，恢复到TPipe的初始化状态。

针对Ascend 950PR/Ascend 950DT，调用该接口后，CTRL[48]保持原值，CTRL[60]复位为1。CTRL寄存器比特位说明请见SetCtrlSpr。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [Init](init.md)（`related`）：Reset 释放资源并恢复 eventId 等初始化状态；Init 定义该初始状态及缓冲配置，因此两者构成 TPipe 重新配置前的直接状态转换。
- [InitBuffer](init_buffer.md)（`related`）：InitBuffer 负责“用于为TQue等队列和TBuf分配内存”；Reset 负责“完成资源的释放与eventId等变量的初始化操作，恢复到TPipe的初始化状态”。
<!-- cannbot:related:end -->
