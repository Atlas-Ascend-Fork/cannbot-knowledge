---
type: API
title: GetExpMaxMinTmpSize
description: 在host侧获取Exp接口预留或申请临时空间的最大和最小值，用于Tiling参数传递
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Exp_interface/GetExpMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetExpMaxMinTmpSize

host侧Tiling接口，用于获取Exp接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：bool GetExpMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Exp接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

返回值：返回true/false，表明是否能正常获取所需最大最小临时空间。在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [Exp](exp.md)（`same_topic`）：Exp 与《GetExpMaxMinTmpSize》的实质衔接是：这些卡直接给出 Exp 的高阶、基础、Reg 与 C 入口及其临时空间契约；所连排障卡均以 Exp 的溢出、下溢、FTZ 或 clamp 行为作为精度根因和修复对象。
- [Exp接口](exp_interface.md)（`same_topic`）：Exp 总页定义 MaxMinTmpSize、FactorSize 与 Exp 调用的完整 workspace 流程。
- [GetExpTmpBufferFactorSize](get_exp_tmp_buffer_factor_size.md)（`same_topic`）：GetExpTmpBufferFactorSize 与《GetExpMaxMinTmpSize》的实质衔接是：该因子查询与 Exp、Exp 接口页及最大最小临时空间查询共同定义固定 UB 容量下单次可计算元素数。
<!-- cannbot:related:end -->
