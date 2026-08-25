---
type: Guide
title: 高阶API迁移指导
description: Ascend C高阶API基本兼容NPU架构版本3510与NPU架构版本2201，部分API进行了扩展。当前3510架构不支持卷积计算类高阶API。
tags: [task.lookup, topic.quality.compatibility.version_migration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/cross_gen_migration_guide/3510_arch_migration/2201_to_3510_guide/advanced_api_migration.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 高阶API迁移指导

Ascend C高阶API基本兼容NPU架构版本3510与NPU架构版本2201，部分API进行了扩展。当前3510架构不支持卷积计算类高阶API。
## Matmul类高阶API
-   支持的数据类型有变化。
数据类型兼容性情况
-   不支持4:2稀疏特性。具体兼容方案请参考4：2结构化稀疏功能。
## 其它高阶API
数学计算
激活函数
数据归一化
量化操作
归约操作
排序操作
索引计算
数据过滤
张量变换
Hccl

<!-- cannbot:related:start -->
## 相关

- [2201到3510架构变更](../2201_to_3510_arch_changes.md)（`related`）：架构变化页解释为何某些 2201 高阶 API 在 3510 上签名、临时空间或能力发生变化。
- [Ascend C API兼容性策略](../../ascend_c_api_compatibility.md)（`related`）：高阶 API 有独立临时空间、tiling 和签名变化，不能仅依赖基础 API 兼容结论。
- [基础API迁移指导](basic_api_migration.md)（`related`）：高级 API 与基础 API 迁移分别处理封装层和底层签名；混合实现需同时执行两份检查。
- [算子编译迁移指导](op_compilation_migration.md)（`related`）：接口改完后还需按 3510 编译配置、产物和注册流程迁移，构成下游工程步骤。
- [跨代迁移指南概述](../../overview.md)（`same_topic`）：跨代迁移指南概述 与《高阶API迁移指导》的实质衔接是：迁移概述把兼容性判断、架构差异、基础/高阶 API 修改和算子编译迁移串成同一套 2201→3510 决策流程。
<!-- cannbot:related:end -->
