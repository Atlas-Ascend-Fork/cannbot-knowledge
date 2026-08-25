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

- [AscAbs](../reg/arithmetic_compute/asc_abs.md)（`same_topic`）：《AscAbsSync》处理“已废弃的按元素取绝对值同步计算接口，请改用asc_abs和asc_sync实现精细化调优。”。《AscAbs》提供“按元素取绝对值，将结果写入目的操作数dst。”，其具体合同或探针直接接入废弃 AscAbsSync 拆分为 AscAbs 与 asc_sync 的迁移合同。
- [AscAbs](../vector_compute/asc_abs.md)（`same_topic`）：《AscAbsSync》处理“已废弃的按元素取绝对值同步计算接口，请改用asc_abs和asc_sync实现精细化调优。”。《AscAbs》提供“asc_abs（矢量计算）”，其具体合同或探针直接接入废弃 AscAbsSync 拆分为 AscAbs 与 asc_sync 的迁移合同。
- [asc_sync（同步）](../sync/asc_sync.md)（`same_topic`）：《AscAbsSync》处理“已废弃的按元素取绝对值同步计算接口，请改用asc_abs和asc_sync实现精细化调优。”。《asc_sync（同步）》提供“等待所有流水线操作完成。”，其具体合同或探针直接接入废弃 AscAbsSync 拆分为 AscAbs 与 asc_sync 的迁移合同。
<!-- cannbot:related:end -->
