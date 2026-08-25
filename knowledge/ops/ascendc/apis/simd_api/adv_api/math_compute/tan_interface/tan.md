---
type: API
title: Tan
description: 按元素对输入数据做正切函数计算，输入值域需在限定范围内。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Tan_interface/Tan.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# Tan

按元素做正切函数计算，基于泰勒展开式实现（涉及伯努利数）。模板参数T支持half/float。

提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetTanMaxMinTmpSize获取。

模板参数isReuseSource预留，传入false即可。接口参数：dstTensor为输出操作数；srcTensor为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。

约束：输入数据限制在(-65504.0, 65504.0)范围内；不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [Cos](../cos_interface/cos.md)（`related`）：自写 tan=sin/cos 时还需处理 cos 近零和误差放大；标准 Tan 是独立基线。
- [GetTanMaxMinTmpSize](get_tan_max_min_tmp_size.md)（`related`）：调用 Tan 前据 shape 计算 workspace。
- [GetTanTmpBufferFactorSize](get_tan_tmp_buffer_factor_size.md)（`related`）：Tan 的 sharedTmpBuffer 重载需要 Host 为 tile 预留足够空间；FactorSize 可在 UB 预算确定时反推出安全 calCount。
- [Sin](../sin_interface/sin.md)（`related`）：Sin/Cos 组合可做公式 A/B，但不能忽略极点边界。
- [Tan接口](tan_interface.md)（`same_topic`）：Tan接口 与《Tan》的实质衔接是：Tan 接口由 Tan 和两种临时空间查询组成；Atan 是反函数，Sin/Cos 卡解释 tan=sin/cos 的输入值域与验证关系。
<!-- cannbot:related:end -->
