---
type: API
title: AscGe
description: Ge（greater than or equal to），逐元素比较src0 >= src1是否成立，成立则输出结果为1，否则输出结果为0，每个元素的比较结果占一个bit。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_ge.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscGe

Ge（greater than or equal to），逐元素比较src0 >= src1是否成立，成立则输出结果为1，否则输出结果为0，每个元素的比较结果占一个bit。计算公式如下：
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src0、src1的起始地址需要32字节对齐。；dst按照小端顺序排序成二进制结果，对应src中相应位置的数据比较结果。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscGeScalar](asc_ge_scalar.md)（`same_topic`）：Ge（greater than or equal to），逐元素比较src0 >= src1是否成立，成立则输出结果为1，否则输出结果为0，每个元素的比较结果占一个bit。；按元素判断src >= value是否成立，若成立则输出结果为1，否则为0。每个元素的比较结果占1个bit。。两卡在 A2/A3 vector_compute C API 中执行相同的逐元素大于等于比较并输出 bit 结果，分别覆盖矢量对矢量和矢量对标量，属于同一 AscGe 计算契约的操作数变体。
<!-- cannbot:related:end -->
