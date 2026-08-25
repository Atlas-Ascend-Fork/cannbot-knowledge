---
type: API
title: Atanh接口
description: 提供Atanh反双曲正切计算接口及其Tiling临时空间大小查询接口，包含Atanh、GetAtanhMaxMinTmpSize等。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Atanh_interface/Atanh_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Atanh接口

提供Atanh反双曲正切计算接口及其Tiling临时空间大小查询接口，包含Atanh、GetAtanhMaxMinTmpSize等。

按元素做反双曲正切余弦函数计算，计算公式如下：

本接口组包含 Atanh。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：输入源数据需保持值域在(-0.99，-0.001)或者(0.001， 0.99)区间内。若输入不在范围内，输出结果无效。；不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [GetAtanhMaxMinTmpSize](get_atanh_max_min_tmp_size.md)（`related`）：Atanh 的临时空间需要由该 Host 查询接口按输入长度和 dtype 计算最大/最小值后分配。
- [GetAtanhTmpBufferFactorSize](get_atanh_tmp_buffer_factor_size.md)（`related`）：《GetAtanhTmpBufferFactorSize》处理“获取Atanh接口的maxLiveNodeCount和extraBuffer，用于推算固定空间下单次最大计算元素数”。《Atanh接口》明确“提供Atanh反双曲正切计算接口及其Tiling临时空间大小查询接口，包含Atanh、GetAtanhMaxMinTmpSize等。”，可直接用于核对Atanh 高阶 Kernel 的临时空间系数、上下界估算和对应标量实现。
- [Atanh](atanh.md)（`same_topic`）：《Atanh》处理“按元素做反双曲正切函数计算，输入值域需在指定区间内”。《Atanh接口》提供“提供Atanh反双曲正切计算接口及其Tiling临时空间大小查询接口，包含Atanh、GetAtanhMaxMinTmpSize等。”，其具体合同或探针直接接入Atanh Kernel 调用、临时空间推导和 SIMT 对应实现。
- [Atanhf](../../../../simt_api/math_functions/float_math_functions/atanhf.md)（`same_topic`）：Atanhf 的核心契约是“获取输入数据的反双曲正切值”；Atanh接口 补充“提供Atanh反双曲正切计算接口及其Tiling临时空间大小查询接口，包含Atanh、GetAtanhMaxMinTmpSize等”。
<!-- cannbot:related:end -->
