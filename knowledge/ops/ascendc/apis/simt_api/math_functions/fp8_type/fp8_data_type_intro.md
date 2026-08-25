---
type: API
title: fp8数据类型简介（FP8类型）
description: SIMT编程支持3种fp8数据类型，分别是float8_e4m3_t、float8_e5m2_t、hifloat8_t。其数据范围如下：
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/fp8_type/fp8_data_type_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# fp8数据类型简介（FP8类型）

功能：SIMT编程支持3种fp8数据类型，分别是float8_e4m3_t、float8_e5m2_t、hifloat8_t。其数据范围如下。float8_e4m3_t：1：4；float8_e5m2_t：1：5；hifloat8_t：1：由点域编码决定。

<!-- cannbot:related:start -->
## 相关

- [AscEnableFp8](../../../simd_api/c_api/cube_compute/asc_enable_fp8.md)（`related`）：FP8 类型说明给出 e4m3/e5m2/HiF8 的数值范围，支撑开启 FP8 模式前选择与输入编码相符的格式。
- [__half22hif82_rh_sat](fp8_conversion_functions/_half22hif82_rh_sat.md)（`related`）：__half22hif82_rh_sat 与《fp8数据类型简介（FP8类型）》的实质衔接是：half2→hif8x2 的 hybrid 舍入+饱和转换与非饱和、RNA、float2 入口、反向转换及 NaN 饱和故障共享编码契约。
- [__e5m2x22float2](fp8_conversion_functions/_e5m2x22float2.md)（`same_topic`）：__e5m2x22float2 与《fp8数据类型简介（FP8类型）》的实质衔接是：该接口把 packed E5M2 两 lane 解码成 float2；E4M3/HIF8/half2 解码、FP8 类型说明和反向编码入口共同限定格式选择与 round/saturation。
<!-- cannbot:related:end -->
