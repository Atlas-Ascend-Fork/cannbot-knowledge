---
type: API
title: SinCos
description: 按元素进行正弦计算和余弦计算，分别获得正弦和余弦的结果。 ! !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/SinCos_interface/SinCos.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# SinCos

按元素同时进行正弦和余弦计算，分别输出正弦结果（dst0）和余弦结果（dst1）。模板参数T支持half/float。仅Ascend 950PR/950DT支持。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetSinCosMaxMinTmpSize获取。

模板参数config为SinCosConfig类型，含isReuseSource（预留，传false）。接口参数：dst0、dst1为两个输出操作数（正弦和余弦结果），TPosition支持VECIN/VECCALC/VECOUT；src为输入操作数，数据类型需与dst一致；sharedTmpBuffer为临时缓存；count为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [Cos](../cos_interface/cos.md)（`related`）：当同一输入同时需要正弦和余弦时 SinCos 可一次生成两路结果；它与只求 Cos 的接口形成具体选型边界。
- [GetSinCosMaxMinTmpSize](get_sin_cos_max_min_tmp_size.md)（`related`）：SinCos 调用所需 workspace 上下界由该接口给出，直接约束临时缓冲分配。
- [GetSinCosTmpBufferFactorSize](get_sin_cos_tmp_buffer_factor_size.md)（`related`）：SinCos 计算需要 sharedTmpBuffer 和 count；FactorSize 的 maxLivedNodeCount/extraBuf 公式正用于确定该 count，能直接避免临时空间不足或除零。
- [SinCos接口](sin_cos_interface.md)（`same_topic`）：SinCos接口 与《SinCos》的实质衔接是：SinCos 接口组以一次调用同时产出 sin/cos，并由两级工作区查询决定 tmpBuffer；Sincosf/Sincospif提供无 π 与带 π 缩放的标量对照。
- [Sincosf](../../../../simt_api/math_functions/float_math_functions/sincosf.md)（`same_topic`）：SIMT sincosf 与高阶 SinCos 都一次返回正弦和余弦，可按编程模型和存储路径选择实现。
- [Sincospif](../../../../simt_api/math_functions/float_math_functions/sincospif.md)（`same_topic`）：Sincospif 与《SinCos》的衔接是：Sincospif 同时计算 sin(pi*x)/cos(pi*x)；Cospif、Sincosf 和高阶 SinCos 分别提供单输出、无 pi 缩放和张量形态的直接对照。
<!-- cannbot:related:end -->
