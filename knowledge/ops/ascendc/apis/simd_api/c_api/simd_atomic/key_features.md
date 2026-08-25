---
type: API
title: 关键特性说明（SIMD原子操作）
description: 确定性计算是指在相同输入条件下，无论执行次数或执行环境如何变化，总能产生完全一致输出结果的计算过程。确定性计算为系统稳定性和实验可验证性提供保障。
tags: [task.lookup, topic.implementation.api_layer.c_api, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/simd_atomic/key_features.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# 关键特性说明（SIMD原子操作）

确定性计算是指在相同输入条件下，无论执行次数或执行环境如何变化，总能产生完全一致输出结果的计算过程。确定性计算为系统稳定性和实验可验证性提供保障。
确定性计算是指在相同输入条件下，无论执行次数或执行环境如何变化，总能产生完全一致输出结果的计算过程。确定性计算为系统稳定性和实验可验证性提供保障。

对下文描述中出现的接口有以下说明：

- 对于浮点数类型的原子累加，本文以asc_set_atomic_add_float()为例，更多原子操作类型参考asc_set_atomic_add。
- 对于原子最大和原子最小，本文以asc_set_atomic_max_float()和asc_set_atomic_min_float()为例，更多原子操作类型参考asc_set_atomic_max和asc_set_atomic_min。
- 对于AIV和AIC中向GM搬运数据的接口，本文分别以asc_copy_ub2gm()和asc_copy_l0c2gm()为例，更多搬运接口参考矢量数据搬运和矩阵数据搬运。

<!-- cannbot:related:start -->
## 相关

- [AscSetAtomicMin](asc_set_atomic_min.md)（`related`）：AscSetAtomicMin 与《关键特性说明（SIMD原子操作）》的实质衔接是：AscSetAtomicMin 开启后续搬出取小，并需用 None 复位；SetAtomicMin/AtomicMin 和 store atomic 配置给出同一原子写回状态机。
<!-- cannbot:related:end -->
