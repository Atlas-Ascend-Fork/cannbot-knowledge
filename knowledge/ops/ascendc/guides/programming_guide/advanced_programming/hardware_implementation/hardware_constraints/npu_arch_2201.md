---
type: Guide
title: NPU架构版本2201
description: 本节介绍硬件约束以及解决方案建议。对应的产品型号为：
tags: [task.lookup, topic.programming_model.execution_unit]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/hardware_implementation/hardware_constraints/npu_arch_2201.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# NPU架构版本2201

本节介绍硬件约束以及解决方案建议。对应的产品型号为：
-   Atlas A3 训练系列产品/Atlas A3 推理系列产品
-   Atlas A2 训练系列产品/Atlas A2 推理系列产品
硬件约束以及解决方案建议

<!-- cannbot:related:start -->
## 相关

- [基础API迁移指导](../../../../cross_gen_migration_guide/3510_arch_migration/2201_to_3510_guide/basic_api_migration.md)（`related`）：基础API迁移指导 与《NPU架构版本2201》的实质衔接是：基础 API 迁移与架构变化、兼容策略及编译/高阶迁移共同组成 2201 到 3510 的改造流程；所连具体卡验证被删除接口、硬件约束和替代调用。
- [避免bank冲突（NPU架构版本2201）](../../../../operator_practice/simd_operator_optimization/memory_access/avoid_ub_bank_conflict/avoid_bank_conflict_npu_arch_2201.md)（`related`）：避免bank冲突（NPU架构版本2201）：2201与3510卡解释不同 UB bank组织，2201架构约束给出硬件前提；同地址访问是正文读写冲突的直接特例，迁移卡说明跨代调整边界。 目标卡《NPU架构版本2201》补充：本节介绍硬件约束以及解决方案建议。对应的产品型号为：
<!-- cannbot:related:end -->
