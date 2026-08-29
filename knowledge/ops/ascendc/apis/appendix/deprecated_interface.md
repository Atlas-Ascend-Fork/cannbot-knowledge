---
type: API
title: 废弃接口
description: 列出Ascend C中已废弃或后续版本将废弃的C API接口，并给出每个接口的推荐替代方案。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/deprecated_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 废弃接口

列出 Ascend C 中已废弃或后续版本将废弃的 C API 接口，并给出每个接口的推荐替代方案。涵盖数据搬运、原子操作、系统变量、Reg 数据搬运、Reg 矢量计算、同步控制与矢量计算等类别。
数据搬运类 asc_set_gm2ub_pad 建议改用 asc_set_copy_pad_val；高维切分搬运形式已废弃，改用 asc_load_l2_cache_mode 与 asc_store_l2_cache_mode 枚举配置 L2 Cache 策略。
原子操作类建议改用 asc_atomic_add、asc_set_atomic_add_int32、asc_set_atomic_max_int32、asc_set_atomic_min_int32 等显式类型版本。
Reg 数据搬运中 asc_loadalign 多模式重载已收窄为 NORM 模式，BRC、UNPACK、DOWN2X 等模式拆分到独立函数；asc_storealign 同样拆分为 NORM、PACK、INTLV 等独立函数。
同步控制类 asc_sync_vec 与矢量计算类 asc_abs_sync 已废弃，统一改用 asc_sync 执行全流水线同步。
