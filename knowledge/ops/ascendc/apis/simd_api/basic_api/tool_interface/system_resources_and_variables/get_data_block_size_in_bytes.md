---
type: API
title: GetDataBlockSizeInBytes
description: 获取当前芯片版本一个DataBlock的大小，单位为Byte。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetDataBlockSizeInBytes.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# GetDataBlockSizeInBytes

头文件路径为："basic_api/kernel_operator_sys_var_intf.h"。

获取当前芯片版本一个DataBlock的大小，单位为Byte。

开发者根据DataBlock的大小来计算API指令中待传入的repeatTime、dstBlkStride、srcblkStride、dstRepStride、srcRepStride等参数值。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。
