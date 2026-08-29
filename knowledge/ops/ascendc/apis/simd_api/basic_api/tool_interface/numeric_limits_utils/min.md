---
type: API
title: Min
description: 返回指定数据类型的最小有限值，浮点类型返回最小规约正数，支持标量和矢量两种接口。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/NumericLimits_utils/Min.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Min

头文件路径为："basic_api/kernel_operator_limits_intf.h"。

返回指定数据类型的最小有限值，对于浮点数类型来说，返回其最小规约正数。

参数：dst(输出): 目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 LocalTensor的起始地址需要32字节对齐。；count(输入): 输入数据元素个数。

支持数据类型：int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float。

约束：标量接口无约束，矢量接口使用duplicate填充前count个元素赋最小有限值，参照Memory矢量计算下的数据填充接口duplicate约束。

仅 Ascend 950PR/Ascend 950DT 支持。
