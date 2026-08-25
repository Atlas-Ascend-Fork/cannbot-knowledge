---
type: API
title: AscGeScalar
description: 按元素判断src >= value是否成立，若成立则输出结果为1，否则为0。每个元素的比较结果占1个bit。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_ge_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscGeScalar

按元素判断src >= value是否成立，若成立则输出结果为1，否则为0。每个元素的比较结果占1个bit。
函数原型：void asc_ge_scalar(__ubuf__ uint8_t* dst, __ubuf__ half* src, half value, uint8_t repeat, uint16_t dst_block_stride, uint16_t src_block_stride, uint16_t dst_repeat_stride, uint16_t src_repeat_stride)
参数：dst（输出）：目的操作数（矢量）的起始地址。；src（输入）：源操作数（矢量）的起始地址。；value（输入）：源操作数（标量）。
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。；dst按照小端顺序排序成二进制结果，对应src中相应位置的数据比较结果。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscNe](asc_ne.md)（`related`）：《AscNe》说明按元素判断src0 != src1是否成立，若成立则输出结果为1，否则为0。每个元素的比较结果占1个bit。 当结果输出到寄存器中时，可在计算完成后调用asc_get_cmp_mask获取比较结果。；《AscGeScalar》说明按元素判断src >= value是否成立，若成立则输出结果为1，否则为0。每个元素的比较结果占1个bit。。二者在AscNe生成1-bit比较结果并通过CMPMASK读取；Reg等价接口、标量变体和Eq/Gt边界用于确认谓词语义上存在可执行的直接衔接。
- [AscEqScalar](asc_eq_scalar.md)（`same_topic`）：AscEqScalar 与《AscGeScalar》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
- [AscGeScalar](../reg/compare_and_select/asc_ge_scalar.md)（`same_topic`）：焦点处理AscGeScalar 的标量比较 mask 及 Select 消费路径；AscGeScalar正文界定“按元素判断src >= value是否成立，若成立则输出结果为1，否则为0。每个元素的比较结果占1个bit”。候选生成相同 GE mask、提供标量 Compares，或由 Select/AscSelect 直接消费比较结果。
<!-- cannbot:related:end -->
