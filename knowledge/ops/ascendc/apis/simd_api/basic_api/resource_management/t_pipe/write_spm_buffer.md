---
type: API
title: WriteSpmBuffer
description: 将UB空间不足时需要溢出暂存的数据拷贝到SPM Buffer中。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/WriteSpmBuffer.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# WriteSpmBuffer

头文件路径为："basic_api/kernel_tpipe.h"。

将因为UB空间不足而需要溢出暂存的数据拷贝到SPM Buffer中。

约束：-   暂存拷贝到L1时注意writeSize和writeOffset保证32字节对齐。
-   拷贝的内存不要超出初始化的SPM Buffer大小，否则会存在溢出踩踏等问题。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [InitSpmBuffer](init_spm_buffer.md)（`related`）：InitSpmBuffer 与《WriteSpmBuffer》的实质衔接是：InitSpmBuffer 创建 GM 上的 SPM 溢出区，Read/WriteSpmBuffer 与 TPipe 生命周期共同构成初始化、访问和销毁链。
- [ReadSpmBuffer](read_spm_buffer.md)（`same_topic`）：WriteSpmBuffer 把 UB 溢出写入 SPM，ReadSpmBuffer 再读回 local；二者组成暂存往返并共享 size/offset 对齐与边界。
<!-- cannbot:related:end -->
