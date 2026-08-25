---
type: API
title: AscNe
description: 按元素判断src0 != src1是否成立，若成立则输出结果为1，否则为0。每个元素的比较结果占1个bit。 当结果输出到寄存器中时，可在计算完成后调用asc_get_cmp_mask获取比较结果。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_ne.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# AscNe

按元素判断src0 != src1是否成立，若成立则输出结果为1，否则为0。每个元素的比较结果占1个bit。 当结果输出到寄存器中时，可在计算完成后调用asc_get_cmp_mask获取比较结果。
函数原型：void asc_ne(__ubuf__ half* src0, __ubuf__ half* src1, uint8_t repeat, uint8_t dst_block_stride, uint8_t src0_block_stride, uint8_t src1_block_stride, uint8_t dst_repeat_stride, uint8_t src0_repeat_stride, uint8_t src1_repeat_stride)
参数：dst（输出）：目的操作数（矢量）的起始地址。；src0（输入）：源操作数（矢量）的起始地址。；src1（输入）：源操作数（矢量）的起始地址。
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src0、src1的起始地址需要32字节对齐。；dst按照小端顺序排序成二进制结果，对应src中相应位置的数据比较结果。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscEq](asc_eq.md)（`related`）：《AscNe》说明按元素判断src0 != src1是否成立，若成立则输出结果为1，否则为0。每个元素的比较结果占1个bit。 当结果输出到寄存器中时，可在计算完成后调用asc_get_cmp_mask获取比较结果。；《AscEq》说明比较src0与src1在对应索引位置的元素大小。若比较结果为真，则输出结果的对应比特位设为1，否则设为0。。二者在AscNe生成1-bit比较结果并通过CMPMASK读取；Reg等价接口、标量变体和Eq/Gt边界用于确认谓词语义上存在可执行的直接衔接。
- [AscGeScalar](asc_ge_scalar.md)（`related`）：《AscNe》说明按元素判断src0 != src1是否成立，若成立则输出结果为1，否则为0。每个元素的比较结果占1个bit。 当结果输出到寄存器中时，可在计算完成后调用asc_get_cmp_mask获取比较结果。；《AscGeScalar》说明按元素判断src >= value是否成立，若成立则输出结果为1，否则为0。每个元素的比较结果占1个bit。。二者在AscNe生成1-bit比较结果并通过CMPMASK读取；Reg等价接口、标量变体和Eq/Gt边界用于确认谓词语义上存在可执行的直接衔接。
- [AscGetCmpMask](asc_get_cmp_mask.md)（`related`）：《AscNe》说明按元素判断src0 != src1是否成立，若成立则输出结果为1，否则为0。每个元素的比较结果占1个bit。 当结果输出到寄存器中时，可在计算完成后调用asc_get_cmp_mask获取比较结果。；《AscGetCmpMask》说明此接口用于获取Compare操作的比较结果。。二者在AscNe生成1-bit比较结果并通过CMPMASK读取；Reg等价接口、标量变体和Eq/Gt边界用于确认谓词语义上存在可执行的直接衔接。
- [AscGt](asc_gt.md)（`related`）：《AscNe》说明按元素判断src0 != src1是否成立，若成立则输出结果为1，否则为0。每个元素的比较结果占1个bit。 当结果输出到寄存器中时，可在计算完成后调用asc_get_cmp_mask获取比较结果。；《AscGt》说明按元素比较两个矢量的大小关系，若比较后的结果为真，则输出结果的对应比特位为1，否则为0。。二者在AscNe生成1-bit比较结果并通过CMPMASK读取；Reg等价接口、标量变体和Eq/Gt边界用于确认谓词语义上存在可执行的直接衔接。
- [AscNe](../reg/compare_and_select/asc_ne.md)（`same_topic`）：《AscNe》说明按元素判断src0 != src1是否成立，若成立则输出结果为1，否则为0。每个元素的比较结果占1个bit。 当结果输出到寄存器中时，可在计算完成后调用asc_get_cmp_mask获取比较结果。；《AscNe》说明逐元素比较两个源操作数是否不相等，比较结果写入目的操作数对应比特位，为真则置1，否则置0。。二者在AscNe生成1-bit比较结果并通过CMPMASK读取；Reg等价接口、标量变体和Eq/Gt边界用于确认谓词语义上存在可执行的直接衔接。
- [AscNeScalar](asc_ne_scalar.md)（`same_topic`）：《AscNe》说明按元素判断src0 != src1是否成立，若成立则输出结果为1，否则为0。每个元素的比较结果占1个bit。 当结果输出到寄存器中时，可在计算完成后调用asc_get_cmp_mask获取比较结果。；《AscNeScalar》说明src中的每个元素逐个与标量value比较大小，如果某个位置上的元素不等于value，则输出结果dst对应比特位为1，否则为0。。二者在AscNe生成1-bit比较结果并通过CMPMASK读取；Reg等价接口、标量变体和Eq/Gt边界用于确认谓词语义上存在可执行的直接衔接。
<!-- cannbot:related:end -->
