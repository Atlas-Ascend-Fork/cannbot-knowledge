---
type: API
title: AscAbsSync
description: 已废弃的按元素取绝对值同步计算接口，请改用asc_abs和asc_sync实现精细化调优。
tags: [task.lookup, topic.quality.compatibility.deprecation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/deprecated_interface/asc_abs_sync_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---
# AscAbsSync

该接口废弃，请通过asc_abs和同步接口asc_sync实现精细化调优，达成最优性能。

按元素取绝对值。

参数：dst(输出): 目的操作数（矢量）的起始地址。；src(输入): 源操作数（矢量）的起始地址。；count(输入): 参与计算的元素个数。

约束：- dst、src的起始地址需要32字节对齐。
- 操作数地址重叠约束

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [asc_sync（同步）](../sync/asc_sync.md)（`related`）：该接口废弃，请通过asc_abs和同步接口asc_sync实现精细化调优，达成最优性能。；等待所有流水线操作完成。。废弃接口把同步职责拆给 asc_sync，目标卡说明其等待全部流水线及性能代价，从而补齐拆分迁移后的顺序保证和调优边界。
- [AscAbs](../vector_compute/asc_abs.md)（`same_topic`）：该接口废弃，请通过asc_abs和同步接口asc_sync实现精细化调优，达成最优性能。；按元素取绝对值，计算公式如下：。废弃接口的计算部分被明确迁移到 asc_abs，目标卡给出该替代接口的 half 数据与 32 字节对齐合同，能直接完成调用迁移。
<!-- cannbot:related:end -->
