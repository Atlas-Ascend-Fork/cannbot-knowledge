---
type: API
title: Sub
description: 双目矢量计算接口，对两个输入tensor按元素求差。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Sub.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Sub

双目矢量计算接口，按元素求差。头文件 `basic_api/kernel_operator_vec_binary_intf.h`。计算公式 dst_i = src0_i - src1_i。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [Vector Sub 源 UB 非 32B 对齐触发错误 340](../../../../../runbooks/compilation/vector_sub_ub_32b_340.md)（`exemplifies`）：Vector Sub 源 UB 非 32B 对齐触发错误 340 与《Sub》的实质衔接是：Vector Sub 的每个 UB 源必须 32B 对齐，LocalTensor 非零 operator[] 偏移会破坏对齐；Sub API、GetWithOffset/TBuf 和相邻未对齐故障卡直接支持定位及对齐搬入修法。
- [Sub](../../reg_vector_compute/basic_arithmetic/sub.md)（`related`）：The Reg-vector Sub performs the same elementwise subtraction in register programming, enabling an execution-model choice against Memory-vector Sub.
- [AscSub](../../../c_api/reg/arithmetic_compute/asc_sub.md)（`same_topic`）：《AscSub》说明根据mask对源操作数src0、src1按元素求差，将结果写入目的操作数dst。可选保留进位到carry寄存器。；《Sub》说明双目矢量计算接口，对两个输入tensor按元素求差。。二者在AscSub在Vector、Reg和Memory层实现同一减法，SubC/Relu融合及UB对齐故障给出结果变体和调用边界上存在可执行的直接衔接。
- [AscSub](../../../c_api/vector_compute/asc_sub.md)（`same_topic`）：AscSub：所选接口共享逐元素减法，覆盖Reg/Memory、标量和ReLU融合原型；alignment runbook直接说明Vector Sub源UB未32B对齐时的340故障与修复前置条件。 目标卡《Sub》补充：双目矢量计算接口，对两个输入tensor按元素求差。
<!-- cannbot:related:end -->
