---
type: API
title: SinCos接口
description: 按元素同时计算正弦和余弦结果，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/SinCos_interface/SinCos_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# SinCos接口

按元素同时计算正弦和余弦结果，并提供临时空间大小获取接口。

按元素进行正弦计算和余弦计算，分别获得正弦和余弦的结果。

本接口组包含 SinCos。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [GetSinCosMaxMinTmpSize](get_sin_cos_max_min_tmp_size.md)（`same_topic`）：SinCos接口 与《GetSinCosMaxMinTmpSize》的实质衔接是：SinCos 接口组以一次调用同时产出 sin/cos，并由两级工作区查询决定 tmpBuffer；Sincosf/Sincospif提供无 π 与带 π 缩放的标量对照。
- [GetSinCosTmpBufferFactorSize](get_sin_cos_tmp_buffer_factor_size.md)（`same_topic`）：SinCos接口 与《GetSinCosTmpBufferFactorSize》的实质衔接是：SinCos 接口组以一次调用同时产出 sin/cos，并由两级工作区查询决定 tmpBuffer；Sincosf/Sincospif提供无 π 与带 π 缩放的标量对照。
- [SinCos](sin_cos.md)（`same_topic`）：SinCos接口 与《SinCos》的实质衔接是：SinCos 接口组以一次调用同时产出 sin/cos，并由两级工作区查询决定 tmpBuffer；Sincosf/Sincospif提供无 π 与带 π 缩放的标量对照。
- [Sincosf](../../../../simt_api/math_functions/float_math_functions/sincosf.md)（`same_topic`）：SinCos接口 与《Sincosf》的实质衔接是：SinCos 接口组以一次调用同时产出 sin/cos，并由两级工作区查询决定 tmpBuffer；Sincosf/Sincospif提供无 π 与带 π 缩放的标量对照。
- [Sincospif](../../../../simt_api/math_functions/float_math_functions/sincospif.md)（`same_topic`）：SinCos接口 与《Sincospif》的实质衔接是：SinCos 接口组以一次调用同时产出 sin/cos，并由两级工作区查询决定 tmpBuffer；Sincosf/Sincospif提供无 π 与带 π 缩放的标量对照。
<!-- cannbot:related:end -->
