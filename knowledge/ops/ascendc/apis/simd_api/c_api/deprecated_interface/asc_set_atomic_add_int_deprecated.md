---
type: API
title: asc_set_atomic_add_int（废弃）
description: 该接口已废弃，请使用asc_set_atomic_add_int32替代。 头文件路径："c_api/atomic/atomic.h"。
  设置对后续的从Unified Buffer/L0C Buffer/L1 Buffer到Global Memory的数据传输开启原子累加。累加的数据类型为int32_t。
tags: [task.lookup, topic.quality.compatibility.deprecation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/deprecated_interface/asc_set_atomic_add_int_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# asc_set_atomic_add_int（废弃）

该接口已废弃，请使用asc_set_atomic_add_int32替代。

设置对后续的从Unified Buffer/L0C Buffer/L1 Buffer到Global Memory的数据传输开启原子累加。累加的数据类型为int32_t。

头文件："c_api/atomic/atomic.h"。

约束：- 使用完成后，建议清空原子操作的状态（
- 该指令执行前不会对GM的数据做清零操作，开发者需在需要时手动添加清零操作。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscSetAtomicNone](../simd_atomic/asc_set_atomic_none.md)（`related`）：设置原子加状态后需用 asc_set_atomic_none 关闭原子模式，避免后续搬运继续累加。
<!-- cannbot:related:end -->
