---
type: API
title: AscStoreDev
description: 不经过DCache直接向Global Memory地址写数据，避免多核操作未对齐Cache Line时的数据随机覆盖问题。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/scalar_compute/asc_store_dev.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscStoreDev

不经过DCache向GM地址上写数据。 当多核操作GM地址时，如果数据无法对齐到Cache Line，经过DCache的方式下，由于按照Cache Line大小进行读写，会导致多核数据随机覆盖的问题。此时，可以采用不经过DCache直接读写GM地址的方式，从而避免上述随机覆盖的问题。
约束：addr起始地址须按写入dtype字节数对齐。；addr须落在GM可访问地址空间内。；本接口运行在标量流水上，与后续依赖该写入结果的指令之间存在标量数据依赖；如后续有读取同一GM地址的指令，须通过同步指令建立依赖顺序，标量流水本身的顺序执行不保证跨指令访存可见性。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoadDev](asc_load_dev.md)（`related`）：AscLoadDev 绕过 DCache 读 GM，AscStoreDev 绕过 DCache 写 GM；多核共享非 Cache-Line 对齐字段时两者形成无缓存的读写对。
- [AscStoreL2CacheMode](../enum/asc_store_l2_cache_mode.md)（`related`）：StoreDev 的 L2 cache mode 决定写是否进入 L2。
- [ReadGmByPassDCache](../../basic_api/scalar_compute/read_gm_by_pass_d_cache_isasi.md)（`related`）：C++ bypass read 与 StoreDev 组成可见性验证。
- [WriteGmByPassDCache](../../basic_api/scalar_compute/write_gm_by_pass_d_cache_isasi.md)（`same_topic`）：WriteGmByPassDCache 与 AscStoreDev 都绕过 DCache 向 GM 写入单个标量，以规避多核共享 Cache Line 的覆盖；平台与地址约束不同，但核心写入语义一致。
<!-- cannbot:related:end -->
