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

- [InitSpmBuffer](init_spm_buffer.md)（`related`）：InitSpmBuffer 与《ReadSpmBuffer》的实质衔接是：InitSpmBuffer 创建 GM 上的 SPM 溢出区，Read/WriteSpmBuffer 与 TPipe 生命周期共同构成初始化、访问和销毁链。
- [WriteSpmBuffer](write_spm_buffer.md)（`same_topic`）：WriteSpmBuffer 把 UB 溢出写入 SPM，ReadSpmBuffer 再读回 local；二者组成暂存往返并共享 size/offset 对齐与边界。
<!-- cannbot:related:end -->
