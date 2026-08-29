---
type: API
title: ReadSpmBuffer
description: 从SPM Buffer读回数据到local内存中。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/ReadSpmBuffer.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# ReadSpmBuffer

头文件路径为："basic_api/kernel_tpipe.h"。

从SPM Buffer读回到local数据中。

参数：T: 待获取Tensor的数据类型，支持的类型请见LocalTensor相关描述。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [InitSpmBuffer](init_spm_buffer.md)（`related`）：初始化SPM Buffer。SPM Buffer是一块在GM上的空间，当UB空间不足时可以将溢出数据存放在SPM Buffer上。；从SPM Buffer读回到local数据中。；焦点建立溢出缓冲，目标接口消费该缓冲并把数据读回 local。
- [WriteSpmBuffer](write_spm_buffer.md)（`same_topic`）：从SPM Buffer读回到local数据中。 将因为UB空间不足而需要溢出暂存的数据拷贝到SPM Buffer中。 WriteSpmBuffer 是 SPM 暂存的 producer，ReadSpmBuffer 是同一数据的 consumer，组成 UB 不足时的写入/回读链。
<!-- cannbot:related:end -->
