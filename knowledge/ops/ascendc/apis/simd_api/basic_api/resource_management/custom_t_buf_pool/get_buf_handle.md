---
type: API
title: GetBufHandle
description: 根据offset取出自定义TBufPool中管理的内存块，返回TBufHandle类型的内存块句柄。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/custom_TBufPool/GetBufHandle.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# GetBufHandle

头文件路径为："basic_api/kernel_tpipe.h"。

根据offset取出自定义TBufPool中管理的内存块。

约束：offset值不可超出EXTERN_IMPL_BUFPOOL中定义的BUFID_SIZE大小，用户可根据需要添加校验。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。
