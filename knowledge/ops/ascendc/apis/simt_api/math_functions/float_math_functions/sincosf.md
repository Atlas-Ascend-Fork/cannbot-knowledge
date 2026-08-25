---
type: API
title: Sincosf
description: 获取输入数据的三角函数正弦值和余弦值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/sincosf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Sincosf

功能：获取输入数据的三角函数正弦值和余弦值。

函数原型：void sincosf(float x, float *s, float *c)

参数：x（输入）源操作数，s（输出）Unified Buffer、Global Memory或栈空间的地址，用于存储输入数据的三角函数正弦值，c（输出）Unified Buffer、Global Memory或栈空间的地址，用于存储输入数据的三角函数余弦值。

返回值：当输入x为inf、-inf、nan时，输出值为nan。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Acosf](acosf.md)（`related`）：Acos 输入域外的处理不能用 sincos 替代；可在合法域做 cos(acos(x)) 验证。
- [GetSinCosMaxMinTmpSize](../../../simd_api/adv_api/math_compute/sin_cos_interface/get_sin_cos_max_min_tmp_size.md)（`same_topic`）：GetSinCosMaxMinTmpSize说明在host侧获取SinCos接口所需的最大和最小临时空间大小，供开发者选择合适的Tiling参数传入kernel侧。
- [GetSinCosTmpBufferFactorSize](../../../simd_api/adv_api/math_compute/sin_cos_interface/get_sin_cos_tmp_buffer_factor_size.md)（`same_topic`）：GetSinCosTmpBufferFactorSize说明获取SinCos接口所需的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。
- [SinCos](../../../simd_api/adv_api/math_compute/sin_cos_interface/sin_cos.md)（`same_topic`）：SIMT sincosf 与高阶 SinCos 都一次返回正弦和余弦，可按编程模型和存储路径选择实现。
- [SinCos接口](../../../simd_api/adv_api/math_compute/sin_cos_interface/sin_cos_interface.md)（`same_topic`）：SinCos接口 与《Sincosf》的实质衔接是：SinCos 接口组以一次调用同时产出 sin/cos，并由两级工作区查询决定 tmpBuffer；Sincosf/Sincospif提供无 π 与带 π 缩放的标量对照。
- [Sincospif](sincospif.md)（`same_topic`）：Sincospif 与《Sincosf》的衔接是：Sincospif 同时计算 sin(pi*x)/cos(pi*x)；Cospif、Sincosf 和高阶 SinCos 分别提供单输出、无 pi 缩放和张量形态的直接对照。
- [数学函数sinf](sinf.md)（`same_topic`）：sinf 只返回正弦，sincosf 对同一 float 输入同时写出正弦与余弦；当调用链还需要 cos 时，后者是避免重复角函数求值的直接替代契约。
<!-- cannbot:related:end -->
