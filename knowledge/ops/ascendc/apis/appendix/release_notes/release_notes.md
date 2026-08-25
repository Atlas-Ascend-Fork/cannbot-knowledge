---
type: API
title: Release Notes
description: 汇总Ascend C API各CANN版本的发布说明，包含版本间接口变更和新特性介绍。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/Release_Notes/release_notes.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Release Notes

汇总 Ascend C API 在各 CANN 版本的发布说明，记录版本间接口变更与新增特性。当前覆盖 CANN 9.0.0 与 CANN 9.1.0 两个版本。

CANN 9.1.0 面向 Ascend 950PR/Ascend 950DT（3510 架构）C API，新增矢量计算（bitsort、mrgsort4、transpose 等）、数据搬运（gm/ub/l1/l0 各级 buffer 间 copy 及格式转换）、标量原子操作、矩阵乘加（mmad 支持 FP8/HiF8/HF32 等混合精度）、同步控制（lock/unlock、核间信号、内存屏障）以及系统变量与缓存控制接口，并修复 9.0.0 中函数命名、类型声明和地址自更新签名问题。
