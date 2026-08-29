---
type: API
title: asc_dcci_entire
description: 该接口用于刷新核内的整个Data Cache，保证数据读取时Cache的一致性。 在SIMT编程中，写入数据时会立即写入Global Memory，使其他核可见，因此不存在核间一致性问题。当从Global
  Memory读取数据时，该数据可能已被其他核修改，此时应使用dcci接口直接访问Global Memory，以获取最新数据。 请注意，该接口耗时较大，性能敏感的场景慎用。
tags: [task.lookup, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/memory_access_functions/asc_dcci_entire.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_dcci_entire

刷新核内整个 Data Cache，保证后续从 Global Memory 读取数据时 Cache 一致性。SIMT 编程中写入数据会立即写入 Global Memory 使其他核可见，但当读取的数据可能已被其他核修改时，需使用 dcci 接口刷新 Data Cache 以获取最新数据。

函数原型：inline void asc_dcci_entire(void *dst)

参数 dst 为 Global Memory 地址。无返回值。该接口耗时较大，性能敏感场景慎用。输入必须为有效的 Global Memory 地址，否则不能保证刷新行为有效。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。需包含头文件 "simt_api/device_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [asc_dcci_single](asc_dcci_single.md)（`related`）：entire 卡说明“刷新核内整个 Data Cache，保证后续从 Global Memory 读取数据时 Cache 一致性。”并警告整缓存代价；single 卡说明“相比 asc_dcci_entire 仅刷新单条 Cache Line，适合轮询标志位等小范围刷新场景。”，给出按一致性范围和性能代价选择的直接分支。
<!-- cannbot:related:end -->
