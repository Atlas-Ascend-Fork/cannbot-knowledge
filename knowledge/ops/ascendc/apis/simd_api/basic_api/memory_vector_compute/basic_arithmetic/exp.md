---
type: API
title: Exp
description: 单目矢量计算接口，对输入tensor按元素取自然指数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Exp.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Exp

单目矢量计算接口，按元素计算自然指数 e^x。头文件 `basic_api/kernel_operator_vec_unary_intf.h`。计算公式 dst_i = e^(src_i)。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 向量管 FTZ 刷新次正规 exp 为零](../../../../../runbooks/precision/ascend950_ftz_exp.md)（`exemplifies`）：该卡给出 3510 Exp 次正规输出 FTZ 的实测阈值和放大验证。
- [Exp](../../reg_vector_compute/basic_arithmetic/exp.md)（`related`）：Memory Exp 与 Reg Exp 都计算自然指数，但前者直接操作 LocalTensor、后者显式管理 RegTensor 和 mask，可据编程模型选择实现。
- [Ln](ln.md)（`related`）：Ln 是 Exp 的反函数，可在有限正常数范围构造往返精度测试。
- [Muls](muls.md)（`related`）：指数类激活常先对输入缩放；Muls 是公式上游构件但不替代 Exp。
- [AscExp](../../../c_api/reg/arithmetic_compute/asc_exp.md)（`same_topic`）：AscExp 与《Exp》的实质衔接是：这些入口都执行逐元素自然指数；高阶/Memory/Reg/C Vector 对应接口给出不同数据承载方式，FTZ 与 sigmoid 溢出卡直接验证次正规和大指数边界。
- [Exp](../../../adv_api/math_compute/exp_interface/exp.md)（`same_topic`）：Exp 与《Exp》的实质衔接是：这些卡直接给出 Exp 的高阶、基础、Reg 与 C 入口及其临时空间契约；所连排障卡均以 Exp 的溢出、下溢、FTZ 或 clamp 行为作为精度根因和修复对象。
<!-- cannbot:related:end -->
