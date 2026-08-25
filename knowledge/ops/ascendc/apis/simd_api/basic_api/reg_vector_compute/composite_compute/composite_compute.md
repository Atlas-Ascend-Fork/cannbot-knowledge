---
type: API
title: 复合计算
description: Reg矢量计算复合运算接口索引页，包含Axpy、AbsSub、ExpSub、MulDstAdd、MulAddDst与MulsCast。
tags: [task.lookup, topic.compute.composite]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/composite_compute/composite_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 复合计算

Reg 矢量复合计算接口集合，将多个基础运算融合为单次寄存器侧调用。含 Axpy、AbsSub、ExpSub、MulDstAdd、MulAddDst、MulsCast 等，覆盖乘加融合、运算+Cast 融合等场景。相比 Memory 版本，Reg 版本减少寄存器与 UB 间的往返搬运，适合对延迟敏感的计算路径。

<!-- cannbot:related:start -->
## 相关

- [复合计算](../../memory_vector_compute/composite_compute/composite_compute.md)（`same_topic`）：复合计算：Reg复合计算与Memory复合计算提供同类融合算术的两条执行路径；前者减少UB往返，后者直接作用LocalTensor，关系用于路线选择而非为每个成员造边。 目标卡《复合计算》补充：矢量复合计算接口集，包含 Axpy、MulAddDst、MulCast、AddRelu、FusedMulAdd 等融合算子接口。
<!-- cannbot:related:end -->
