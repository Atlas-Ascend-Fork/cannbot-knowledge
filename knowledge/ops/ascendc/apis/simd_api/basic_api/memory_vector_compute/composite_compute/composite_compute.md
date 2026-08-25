---
type: API
title: 复合计算
description: 矢量复合计算接口集，包含 Axpy、MulAddDst、MulCast、AddRelu、FusedMulAdd 等融合算子接口。
tags: [task.lookup, topic.compute.composite]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/composite_compute/composite_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 复合计算

Memory 矢量复合计算接口集合，将多个基础运算融合为单次调用以减少访存与提升性能。包含乘加融合（MulAddDst、FusedMulAdd、MulAddRelu）、运算+激活融合（AddRelu、SubRelu、AddReluCast、SubReluCast）、运算+Cast 融合（MulCast、MulsCast）、量化反量化（CastDequant、AddDeqRelu）及 Axpy、AbsSub、ExpSub 等。ISASI 标记接口为 ISASI 专属扩展。

<!-- cannbot:related:start -->
## 相关

- [复合计算](../../reg_vector_compute/composite_compute/composite_compute.md)（`same_topic`）：复合计算：Reg复合计算与Memory复合计算提供同类融合算术的两条执行路径；前者减少UB往返，后者直接作用LocalTensor，关系用于路线选择而非为每个成员造边。 目标卡《复合计算》补充：矢量复合计算接口集，包含 Axpy、MulAddDst、MulCast、AddRelu、FusedMulAdd 等融合算子接口。
<!-- cannbot:related:end -->
