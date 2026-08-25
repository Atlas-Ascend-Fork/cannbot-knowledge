---
type: API
title: Tan接口
description: 按元素做正切函数计算，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Tan_interface/Tan_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Tan接口

按元素做正切函数计算，并提供临时空间大小获取接口。

按元素做正切函数计算，计算公式如下： Tan(x)的泰勒展开式为： 其中B 2n 是伯努利数。

本接口组包含 Tan。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：输入数据限制在(-65504.0, 65504.0)范围内。；不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core, Kirin X90。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Atan接口](../atan_interface/atan_interface.md)（`same_topic`）：Tan接口 与《Atan接口》的实质衔接是：Tan 接口由 Tan 和两种临时空间查询组成；Atan 是反函数，Sin/Cos 卡解释 tan=sin/cos 的输入值域与验证关系。
- [Cos](../cos_interface/cos.md)（`same_topic`）：Tan接口 与《Cos》的实质衔接是：Tan 接口由 Tan 和两种临时空间查询组成；Atan 是反函数，Sin/Cos 卡解释 tan=sin/cos 的输入值域与验证关系。
- [Cos接口](../cos_interface/cos_interface.md)（`same_topic`）：Tan接口 与《Cos接口》的实质衔接是：Tan 接口由 Tan 和两种临时空间查询组成；Atan 是反函数，Sin/Cos 卡解释 tan=sin/cos 的输入值域与验证关系。
- [GetTanMaxMinTmpSize](get_tan_max_min_tmp_size.md)（`same_topic`）：Tan接口 与《GetTanMaxMinTmpSize》的实质衔接是：Tan 接口由 Tan 和两种临时空间查询组成；Atan 是反函数，Sin/Cos 卡解释 tan=sin/cos 的输入值域与验证关系。
- [GetTanTmpBufferFactorSize](get_tan_tmp_buffer_factor_size.md)（`same_topic`）：Tan接口 与《GetTanTmpBufferFactorSize》的实质衔接是：Tan 接口由 Tan 和两种临时空间查询组成；Atan 是反函数，Sin/Cos 卡解释 tan=sin/cos 的输入值域与验证关系。
- [Sin](../sin_interface/sin.md)（`same_topic`）：Tan接口 与《Sin》的实质衔接是：Tan 接口由 Tan 和两种临时空间查询组成；Atan 是反函数，Sin/Cos 卡解释 tan=sin/cos 的输入值域与验证关系。
- [Tan](tan.md)（`same_topic`）：Tan接口 与《Tan》的实质衔接是：Tan 接口由 Tan 和两种临时空间查询组成；Atan 是反函数，Sin/Cos 卡解释 tan=sin/cos 的输入值域与验证关系。
<!-- cannbot:related:end -->
