---
type: API
title: AscAbs
description: asc_abs（矢量计算）
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_abs.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscAbs

按元素取绝对值，计算公式如下：
函数原型：void asc_abs(__ubuf__ half* dst, __ubuf__ half* src, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscAbsSync](../deprecated_interface/asc_abs_sync_deprecated.md)（`same_topic`）：该接口废弃，请通过asc_abs和同步接口asc_sync实现精细化调优，达成最优性能。；按元素取绝对值，计算公式如下：。废弃接口的计算部分被明确迁移到 asc_abs，目标卡给出该替代接口的 half 数据与 32 字节对齐合同，能直接完成调用迁移。
<!-- cannbot:related:end -->
