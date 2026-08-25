---
type: API
title: AscNeScalar
description: src中的每个元素逐个与标量value比较大小，如果某个位置上的元素不等于value，则输出结果dst对应比特位为1，否则为0。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_ne_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscNeScalar

src中的每个元素逐个与标量value比较大小，如果某个位置上的元素不等于value，则输出结果dst对应比特位为1，否则为0。
函数原型：void asc_ne_scalar(__ubuf__ uint8_t *dst, __ubuf__ half *src, half value, uint8_t repeat, uint16_t dst_block_stride, uint16_t src_block_stride, uint16_t dst_repeat_stride, uint16_t src_repeat_stride)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。；dst按照小端顺序排序成二进制结果，对应src中相应位置的数据比较结果。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscEqScalar](asc_eq_scalar.md)（`related`）：EqScalar 与 NeScalar 共享标量比较和 bit 结果布局，提供互补的相等/不等分支。
- [AscNeScalar](../reg/compare_and_select/asc_ne_scalar.md)（`related`）：Reg 版本执行相同 vector-scalar 不等比较，但输入输出驻留寄存器；Memory 版本操作 UB 指针。
- [AscNe](asc_ne.md)（`same_topic`）：《AscNe》说明按元素判断src0 != src1是否成立，若成立则输出结果为1，否则为0。每个元素的比较结果占1个bit。 当结果输出到寄存器中时，可在计算完成后调用asc_get_cmp_mask获取比较结果。；《AscNeScalar》说明src中的每个元素逐个与标量value比较大小，如果某个位置上的元素不等于value，则输出结果dst对应比特位为1，否则为0。。二者在AscNe生成1-bit比较结果并通过CMPMASK读取；Reg等价接口、标量变体和Eq/Gt边界用于确认谓词语义上存在可执行的直接衔接。
<!-- cannbot:related:end -->
