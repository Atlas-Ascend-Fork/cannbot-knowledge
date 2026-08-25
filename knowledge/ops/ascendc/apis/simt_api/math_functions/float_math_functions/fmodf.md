---
type: API
title: Fmodf
description: 获取输入数据x除以y的余数。求余数时，商取x除以y浮点数结果的整数部分。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/fmodf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Fmodf

功能：获取输入数据x除以y的余数。求余数时，商取x除以y浮点数结果的整数部分。

函数原型：float fmodf(float x, float y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：输入数据x除以y的余数。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Fmod接口](../../../simd_api/adv_api/math_compute/fmod_interface/fmod_interface.md)（`related`）：Fmodf 与 SIMD 高阶 Fmod 都计算截断除法语义的浮点余数，分别适合 SIMT 标量线程和 LocalTensor 向量路径。
- [GetFmodTmpBufferFactorSize](../../../simd_api/adv_api/math_compute/fmod_interface/get_fmod_tmp_buffer_factor_size.md)（`related`）：GetFmodTmpBufferFactorSize 与《Fmodf》的实质衔接是：Fmod 的 factor-size、max/min 临时空间、kernel 接口和标量实现共同决定固定 UB 下单次元素数及除零保护。
- [Remainderf](remainderf.md)（`related`）：Remainderf 与 Fmodf 都返回 x/y 的浮点余数，但前者把商舍入到最近整数且 ties-to-even，后者直接截取商的整数部分；并列阅读可避免在负数和半整数商处误选接口。
- [Remquof](remquof.md)（`related`）：焦点处理remquof 的余数、最近偶数商与 quo 输出语义；Fmodf正文说明“同为浮点余数，但商向零截断；与 Remquof 的最近偶数商构成关键选择边界”。候选与 remquof 共享余数公式或给出其函数族入口，并明确商取整规则的差异。
<!-- cannbot:related:end -->
