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

- [2201到3510架构变更](../2201_to_3510_arch_changes.md)（`related`）：焦点卡写明“AIV核采用Regbase架构，与NPU架构版本2201的Membase架构相比”，候选卡写明“当前3510架构不支持卷积计算类高阶API”。架构卡解释底层代际差异，迁移卡给出高阶 API 兼容例外，把架构变化落实到接口检查。
<!-- cannbot:related:end -->
