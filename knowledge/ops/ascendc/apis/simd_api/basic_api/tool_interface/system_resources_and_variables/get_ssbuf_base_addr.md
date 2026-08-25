---
type: API
title: GetSsbufBaseAddr
description: 获取SSBuffer的基地址。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetSsbufBaseAddr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# GetSsbufBaseAddr

头文件路径为："basic_api/kernel_operator_sys_var_intf.h"。

该接口用于获取SSBuffer的基地址。

约束：- SSBuffer中存在脏数据，读取时数据不保证全为0。
- AIC和AIV启动不同的任务时，不能访问SSBuffer。
- 访问超过最末端的地址存在异常。每个核在非MIX模式下运行时，可以独立占用1KB的空间（AIC，AIV0，AIV1各占据1KB）；或者在MIX模式下运行时共享整个3KB的空间(AIC:AIV = 1:2)。目前SSBuffer的大小为3KB。
- SSBuffer只支持通过读写指令32字节的对齐访问。

仅 Ascend 950PR/Ascend 950DT 支持。
