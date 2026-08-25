---
type: API
title: Mul
description: 双目矢量计算接口，对两个输入tensor按元素求积。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Mul.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Mul

双目矢量计算接口，按元素相乘。头文件 `basic_api/kernel_operator_vec_binary_intf.h`。计算公式 dst_i = src0_i * src1_i。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [BilinearInterpolation](bilinear_interpolation_isasi.md)（`related`）：双线性插值由若干权重乘法和加法组成，Mul 是其基础计算构件但不包含坐标/权重契约。
- [AscMul](../../../c_api/vector_compute/asc_mul.md)（`same_topic`）：AscMul 与《Mul》的实质衔接是：AscMul 是 UB 向量逐元素乘法；Reg/Memory 对应入口与 scalar 变体覆盖不同承载方式，FMA 舍入和 cyclic scale 卡限定不可等价替换与广播范围。
- [Mul](../../reg_vector_compute/basic_arithmetic/mul.md)（`same_topic`）：Mul 与《Mul》的实质衔接是：Reg Mul 的 masked 写入受 MaskMergeMode 控制；Memory Mul、Reg C API AscMul 和 Vector C API AscMul 执行同一逐元素乘法，但操作数位置、执行层与掩码接口不同。
<!-- cannbot:related:end -->
