---
type: API
title: Erfc接口
description: 按元素计算x的互补误差函数，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Erfc_interface/Erfc_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Erfc接口

按元素计算x的互补误差函数，并提供临时空间大小获取接口。

返回输入x的互补误差函数结果，积分区间为x到无穷大。原始的理论计算公式如下： 由于Erfc函数没有初等函数表达方式，一般通过函数逼近的方式计算，近似计算公式如下所示： 其中， R(z) = (((((((z * R0 + R1) * z + R2) * z + R3) * z + R4) * z + R5) * z + R6) * z + R7) * z + R8是关于z的8次多项式； S(z) = ((((z + S1) * z + S2) * z + S3) * z + S4) * z + S5是关于z的4次多项式。

本接口组包含 Erfc。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：输入源数据需保持值域在[-inf, inf]。若输入不在范围内，输出结果无效。；不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core, Kirin X90。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [AscendC GELU 三系数 erfc 在大值域 fp32 精度不足](../../../../../runbooks/precision/gelu_erfc_polynomial_precision_budget.md)（`exemplifies`）：Erfc接口 与《AscendC GELU 三系数 erfc 在大值域 fp32 精度不足》的实质衔接是：Erfc 接口组由实际 Erfc、工作区上限/下限查询和 factor 查询组成；SIMT Erfcf提供标量对照，两张 GELU 卡直接讨论以 erfc 逼近实现时的精度与负尾相消。
- [GELU 负尾部用 erfc 形态避免大数相消](../../../../../runbooks/precision/gelu_negative_tail_erfc_avoids_cancellation.md)（`exemplifies`）：《Erfc接口》明确“按元素计算x的互补误差函数，并提供临时空间大小获取接口。”；它与《GELU 负尾部用 erfc 形态避免大数相消》的“fp32 exact GELU 用 0.5x 加减近等幅项会在负大值尾部相消；直接计算 max(x,0)-0.5|x|erfc(|x|/sqrt(2)) 后 20/20。”在实际调用参数、数据流或结果校验上直接衔接。
- [Erfc](erfc.md)（`same_topic`）：Erfc接口 与《Erfc》的实质衔接是：Erfc 接口组由实际 Erfc、工作区上限/下限查询和 factor 查询组成；SIMT Erfcf提供标量对照，两张 GELU 卡直接讨论以 erfc 逼近实现时的精度与负尾相消。
- [Erfcf](../../../../simt_api/math_functions/float_math_functions/erfcf.md)（`same_topic`）：高阶 Erfc 对 LocalTensor 批量计算互补误差函数，SIMT erfc 对线程标量计算相同数学函数；两卡描述同一 erfc 数值语义，只是执行粒度不同。
- [GetErfcMaxMinTmpSize](get_erfc_max_min_tmp_size.md)（`same_topic`）：Erfc接口 与《GetErfcMaxMinTmpSize》的实质衔接是：Erfc 接口组由实际 Erfc、工作区上限/下限查询和 factor 查询组成；SIMT Erfcf提供标量对照，两张 GELU 卡直接讨论以 erfc 逼近实现时的精度与负尾相消。
- [GetErfcTmpBufferFactorSize](get_erfc_tmp_buffer_factor_size.md)（`same_topic`）：Erfc接口 与《GetErfcTmpBufferFactorSize》的实质衔接是：Erfc 接口组由实际 Erfc、工作区上限/下限查询和 factor 查询组成；SIMT Erfcf提供标量对照，两张 GELU 卡直接讨论以 erfc 逼近实现时的精度与负尾相消。
<!-- cannbot:related:end -->
