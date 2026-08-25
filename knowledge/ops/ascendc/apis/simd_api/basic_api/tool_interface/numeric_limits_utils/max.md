---
type: API
title: Max
description: 返回指定数据类型的最大有限值，支持标量和矢量两种接口，矢量接口为dst前count个元素赋最大有限值。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/NumericLimits_utils/Max.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Max

头文件路径为："basic_api/kernel_operator_limits_intf.h"。

返回指定数据类型的最大有限值。

参数：dst(输出): 目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 LocalTensor的起始地址需要32字节对齐。；count(输入): 输入数据元素个数。

支持数据类型：int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float。

约束：标量接口无约束，矢量接口使用duplicate填充前count个元素赋最大有限值，参照Memory矢量计算下的数据填充接口duplicate约束。

仅 Ascend 950PR/Ascend 950DT 支持。
