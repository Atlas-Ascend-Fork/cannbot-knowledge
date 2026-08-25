---
type: API
title: AscSub
description: asc_sub（矢量计算）
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_sub.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscSub

执行矢量减法运算。计算公式如下：
函数原型：void asc_sub(__ubuf__ int16_t* dst, __ubuf__ int16_t* src0, __ubuf__ int16_t* src1, uint32_t count)
约束：dst、src0、src1的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [Vector Sub 源 UB 非 32B 对齐触发错误 340](../../../../runbooks/compilation/vector_sub_ub_32b_340.md)（`exemplifies`）：AscSub：所选接口共享逐元素减法，覆盖Reg/Memory、标量和ReLU融合原型；alignment runbook直接说明Vector Sub源UB未32B对齐时的340故障与修复前置条件。 目标卡《Vector Sub 源 UB 非 32B 对齐触发错误 340》补充：Ascend950/arch35 上用 AscendC::Sub Level 2 接口对 LocalTensor 做相邻元素差分时，若某个源是 LocalTensor::operator[] 的非零偏移切片（如 rpLocal[1]，偏移 1×sizeof(int32_t)=4 字节），起始地址不满足 Vector 指令 32B 对齐要求，运行时触发错误码 507035、plog 报 errcode:(340) The instruct
- [AscSub](../reg/arithmetic_compute/asc_sub.md)（`same_topic`）：AscSub：所选接口共享逐元素减法，覆盖Reg/Memory、标量和ReLU融合原型；alignment runbook直接说明Vector Sub源UB未32B对齐时的340故障与修复前置条件。 目标卡《AscSub》补充：根据mask对源操作数src0、src1按元素求差，将结果写入目的操作数dst。可选保留进位到carry寄存器。
- [AscSubRelu](asc_sub_relu.md)（`same_topic`）：AscSub：所选接口共享逐元素减法，覆盖Reg/Memory、标量和ReLU融合原型；alignment runbook直接说明Vector Sub源UB未32B对齐时的340故障与修复前置条件。 目标卡《AscSubRelu》补充：按元素求差，再进行Relu计算（结果和0对比取较大值），并提供转换最终结果的数据类型的功能(s162s8、f322f16、f162s8)。
- [AscSubScalar](asc_sub_scalar.md)（`same_topic`）：AscSub：所选接口共享逐元素减法，覆盖Reg/Memory、标量和ReLU融合原型；alignment runbook直接说明Vector Sub源UB未32B对齐时的340故障与修复前置条件。 目标卡《AscSubScalar》补充：执行矢量和标量的减法运算。
- [Sub](../../basic_api/memory_vector_compute/basic_arithmetic/sub.md)（`same_topic`）：AscSub：所选接口共享逐元素减法，覆盖Reg/Memory、标量和ReLU融合原型；alignment runbook直接说明Vector Sub源UB未32B对齐时的340故障与修复前置条件。 目标卡《Sub》补充：双目矢量计算接口，对两个输入tensor按元素求差。
- [Sub](../../basic_api/reg_vector_compute/basic_arithmetic/sub.md)（`same_topic`）：AscSub：所选接口共享逐元素减法，覆盖Reg/Memory、标量和ReLU融合原型；alignment runbook直接说明Vector Sub源UB未32B对齐时的340故障与修复前置条件。 目标卡《Sub》补充：根据mask对源操作数srcReg0、srcReg1按元素求差，将结果写入目的操作数dstReg。可选保留进位到carry寄存器。
<!-- cannbot:related:end -->
