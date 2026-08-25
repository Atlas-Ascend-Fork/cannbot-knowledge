---
type: API
title: QuietNaN
description: 返回指定数据类型的安静NaN值，支持标量和矢量两种接口，矢量接口为dstLocal前count个元素赋安静NaN值。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/NumericLimits_utils/QuietNaN.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# QuietNaN

头文件路径为："basic_api/kernel_operator_limits_intf.h"。

返回指定数据类型的安静NaN值（浮点尾数最高位为1）。

参数：dstLocal(输出): 目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 LocalTensor的起始地址需要32字节对齐。；count(输入): 输入数据元素个数。

支持数据类型：half、bfloat16_t、float。

约束：标量接口无约束，矢量接口使用duplicate填充前count个元素赋安静NaN值，参照Memory矢量计算下的数据填充接口duplicate约束。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [SignalingNaN](signaling_na_n.md)（`related`）：《QuietNaN》明确“返回指定数据类型的安静NaN值，支持标量和矢量两种接口，矢量接口为dstLocal前count个元素赋安静NaN值。”；它与《SignalingNaN》的“返回指定数据类型的发信NaN值（浮点尾数最高位为0），提供标量和矢量两种接口。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
