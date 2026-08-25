---
type: API
title: Acosf
description: 获取输入数据的反余弦值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/acosf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Acosf

功能：获取输入数据的反余弦值。  arcsin(x)为反正弦函数的计算。

函数原型：float acosf(float x)

参数：x（输入）源操作数。

返回值：输入数据的反余弦值。特殊值：inf→nan；-inf→nan；nan→nan。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [GetAcosMaxMinTmpSize](../../../simd_api/adv_api/math_compute/acos_interface/get_acos_max_min_tmp_size.md)（`related`）：GetAcosMaxMinTmpSize 与《Acosf》的实质衔接是：Acos 的 host 临时空间查询必须与 kernel Acos、接口封装及 factor-size 推算使用同一 shape/typeSize/复用策略。
- [Sincosf](sincosf.md)（`related`）：Acos 输入域外的处理不能用 sincos 替代；可在合法域做 cos(acos(x)) 验证。
- [Acos接口](../../../simd_api/adv_api/math_compute/acos_interface/acos_interface.md)（`same_topic`）：高阶 Tensor Acos 与 SIMT acosf 完成同一反余弦任务。
<!-- cannbot:related:end -->
