---
type: API
title: Xor接口
description: 按元素执行异或（Xor）运算，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Xor_interface/Xor_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Xor接口

按元素执行异或（Xor）运算，并提供临时空间大小获取接口。

按元素执行Xor运算，Xor（异或）的概念和运算规则如下： - 概念：参加运算的两个数据，按二进制位进行“异或”运算。 - 运算规则：0^0=0；0^1=1；1^0=1；1^1=0；即：参加运算的两个对象，如果两个相应位为“异”（值不同），则该位结果为1，否则为0【同0异1】。 计算公式如下：

本接口组包含 Xor。

本接口属于高阶数学计算接口。

支持的数据类型为 int16_t、uint16_t。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：不支持源操作数与目的操作数地址重叠。；当前仅支持ND格式的输入，不支持其他格式。；calCount需要保证小于或等于src0Tensor和src1Tensor和dstTensor存储的元素范围。；对于不带calCount参数的接口，需要保证src0Tensor和src1Tensor的shape大小相等。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
