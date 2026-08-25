---
type: API
title: Erf接口
description: 按元素做误差函数（高斯误差函数）计算，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Erf_interface/Erf_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Erf接口

按元素做误差函数（高斯误差函数）计算，并提供临时空间大小获取接口。

按元素做误差函数计算（也称为高斯误差函数，error function or Gauss error function）。计算公式如下：

本接口组包含 Erf。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：不支持源操作数与目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core, Kirin X90。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 Reg 命名空间无 Erf/Tanh 封装](../../../../../runbooks/compilation/ascend950_reg_erf_tanh.md)（`exemplifies`）：Ascend950 Reg 命名空间无 Erf/Tanh 封装说明Ascend950/dav-3510 的 AscendC::Reg 一元运算头文件仅声明 Abs/Relu/Exp/Sqrt/Ln/Log/Log2/Log10/Neg/Not 十种操作，不含 Erf/Tanh/Sigmoid 等超越函数；在 Reg API 策略下实现 GELU exact 模式需将 erf 分解为多项式 + Exp + Mul + Add 组合。
- [GELU 负尾部用 erfc 形态避免大数相消](../../../../../runbooks/precision/gelu_negative_tail_erfc_avoids_cancellation.md)（`exemplifies`）：GELU 负尾部用 erfc 形态避免大数相消说明fp32 exact GELU 用 0.5x 加减近等幅项会在负大值尾部相消；直接计算 max(x,0)-0.5|x|erfc(|x|/sqrt(2)) 后 20/20。
- [Erfinvf](../../../../simt_api/math_functions/float_math_functions/erfinvf.md)（`related`）：《Erfinvf》的任务是“获取输入数据的逆误差函数值。”。《Erf接口》具体提供“按元素做误差函数（高斯误差函数）计算，并提供临时空间大小获取接口。”，它直接用于逆误差函数与正向/互补逆函数的数值关系。
- [数学函数erff](../../../../simt_api/math_functions/float_math_functions/erff.md)（`related`）：erff 提供 float 标量的 SIMT 高斯误差函数及 ±inf/NaN 边界语义；Erf 高阶接口提供 LocalTensor 逐元素计算和临时空间契约。两者计算同一数学函数，但分别服务标量 SIMT 与张量 SIMD 路径，可直接支撑实现路线选择和边界结果对照。
- [Erf](erf.md)（`same_topic`）：Erf说明按元素做误差函数计算，也称为高斯误差函数。
- [GetErfMaxMinTmpSize](get_erf_max_min_tmp_size.md)（`same_topic`）：GetErfMaxMinTmpSize 与《Erf接口》的衔接是：Erf 临时空间查询以 ErfMaxMinTmpSize 的计算因子和接口约束为依据，查询结果直接决定 Erf 调用可安全使用的 tmpBuffer 大小。
- [GetErfTmpBufferFactorSize](get_erf_tmp_buffer_factor_size.md)（`same_topic`）：GetErfTmpBufferFactorSize说明获取Erf接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量。
<!-- cannbot:related:end -->
