---
type: API
title: asc_sync（同步）
description: 等待所有流水线操作完成。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sync/asc_sync.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# asc_sync（同步）

等待所有流水线操作完成。
函数原型：void asc_sync()
约束：asc_sync会等待所有流水线中所有先前提交的接口完成，这会对性能产生影响。若仅需阻塞单条流水线，应避免随意调用asc_sync，可选用asc_sync_pipe、asc_sync_mte2、asc_sync_mte3等接口精准控制，以提升性能。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [AscAbsSync](../deprecated_interface/asc_abs_sync_deprecated.md)（`related`）：该接口废弃，请通过asc_abs和同步接口asc_sync实现精细化调优，达成最优性能。；等待所有流水线操作完成。。废弃接口把同步职责拆给 asc_sync，目标卡说明其等待全部流水线及性能代价，从而补齐拆分迁移后的顺序保证和调优边界。
<!-- cannbot:related:end -->
