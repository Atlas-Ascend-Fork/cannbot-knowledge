---
type: API
title: Atan2f
description: 获取输入数据y/x的反正切值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/atan2f.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Atan2f

功能：获取输入数据y/x的反正切值。

函数原型：float atan2f(float y, float x)

参数：y（输入）源操作数，x（输入）源操作数。

返回值：y/x的反正切值。特殊值：(任意值,nan)→nan；nan→nan；(正值（含+0）,+0)→+0；(正值（含+0）,-0)→-0；(负值（含-0）,+0)→π；(负值（含-0）,-0)→-π；inf→π/4；inf→-π/4。

约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：本接口内部实现使用到了除法运算符，由于除法运算符不支持Subnormal场景，当x和y均为Subnormal数据时，本接口最终返回nan；当仅y为Subnormal数据且x为正数且非Subnormal数据时，本接口最终返回0；当仅y为Subnormal数据且x为负数且非Subnormal数据时，本接口最终返回与y同号的π。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Atan接口](../../../simd_api/adv_api/math_compute/atan_interface/atan_interface.md)（`related`）：《Atan接口》处理“提供Atan反正切计算接口及其Tiling临时空间大小查询接口，包含Atan、GetAtanMaxMinTmpSize等。”。《Atan2f》明确提供“获取输入数据y/x的反正切值。”，其参数、调用或验证步骤直接接入Atan Kernel 调用、临时空间查询和 SIMT 对应实现。
<!-- cannbot:related:end -->
