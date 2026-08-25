---
type: API
title: Lrintf
description: 获取与输入数据最接近的整数，若存在两个同样接近的整数，则获取其中的偶数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/lrintf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Lrintf

功能：获取与输入数据最接近的整数，若存在两个同样接近的整数，则获取其中的偶数。

函数原型：long int lrintf(float x)

参数：x（输入）源操作数。

返回值：与输入浮点数最接近的整数值。特殊值：0→0；0→0；nan→0。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Hrint](../bfloat16_type/bfloat16_math_functions/hrint.md)（`related`）：Hrint 与《Lrintf》的实质衔接是：bfloat16 Hrint 与 half/float rint 及高层 Rint 临时空间接口共享 ties-to-even 任务，类型总览用于对照特殊值和返回精度。
- [Nearbyintf](nearbyintf.md)（`related`）：lrintf 采用相同最近整数规则但把结果转换为 long，返回类型决定后续溢出和存储语义。
- [Llrintf](llrintf.md)（`same_topic`）：Llrintf 与《Lrintf》的实质衔接是：Llrintf 按当前 rounding mode 返回 long long；Lrintf、Rintf/Nearbyintf 和 AscRint分别对照返回宽度、异常行为和 Tensor 入口。
<!-- cannbot:related:end -->
