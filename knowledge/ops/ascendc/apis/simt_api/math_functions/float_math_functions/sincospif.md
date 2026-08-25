---
type: API
title: Sincospif
description: 获取输入数据与π相乘的三角函数正弦值和余弦值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/sincospif.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Sincospif

功能：获取输入数据与π相乘的三角函数正弦值和余弦值。

函数原型：void sincospif(float x, float *s, float *c)

参数：x（输入）源操作数，s（输出）Unified Buffer、Global Memory或栈空间的地址，用于存储输入数据与π相乘的三角函数正弦值，c（输出）Unified Buffer、Global Memory或栈空间的地址，用于存储输入数据与π相乘的三角函数余弦值。

返回值：当x*π超出float最大范围或超出float最小范围时，输出值为nan；当输入x为inf、-inf、nan时，输出值为nan。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Cospif](cospif.md)（`same_topic`）：Sincospif 与《Cospif》的衔接是：Sincospif 同时计算 sin(pi*x)/cos(pi*x)；Cospif、Sincosf 和高阶 SinCos 分别提供单输出、无 pi 缩放和张量形态的直接对照。
- [SinCos](../../../simd_api/adv_api/math_compute/sin_cos_interface/sin_cos.md)（`same_topic`）：Sincospif 与《SinCos》的衔接是：Sincospif 同时计算 sin(pi*x)/cos(pi*x)；Cospif、Sincosf 和高阶 SinCos 分别提供单输出、无 pi 缩放和张量形态的直接对照。
- [SinCos接口](../../../simd_api/adv_api/math_compute/sin_cos_interface/sin_cos_interface.md)（`same_topic`）：SinCos接口 与《Sincospif》的实质衔接是：SinCos 接口组以一次调用同时产出 sin/cos，并由两级工作区查询决定 tmpBuffer；Sincosf/Sincospif提供无 π 与带 π 缩放的标量对照。
- [Sincosf](sincosf.md)（`same_topic`）：Sincospif 与《Sincosf》的衔接是：Sincospif 同时计算 sin(pi*x)/cos(pi*x)；Cospif、Sincosf 和高阶 SinCos 分别提供单输出、无 pi 缩放和张量形态的直接对照。
- [Sinpif](sinpif.md)（`same_topic`）：Sinpif 是 Sincospif 的第一个输出；后者在同一输入上同时计算 sin(pi*x) 与 cos(pi*x)，可直接复用特殊值和 π 缩放验证。
<!-- cannbot:related:end -->
