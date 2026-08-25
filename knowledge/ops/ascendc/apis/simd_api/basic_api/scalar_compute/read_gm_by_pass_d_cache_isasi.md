---
type: API
title: ReadGmByPassDCache
description: 不经过DCache从GM地址读取数据。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/scalar_compute/ReadGmByPassDCache_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# ReadGmByPassDCache

头文件路径为："basic_api/kernel_operator_scalar_intf.h"。

不经过DCache从GM地址上读数据。

参数：T: 操作数的数据类型。；addr(输入): 源GM地址。

支持数据类型：支持的数据类型为int8_t、uint8_t、int16_t、uint16_t、int32_t、uint32_t、int64_t、uint64_t。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscAtomicSub](../../c_api/scalar_compute/asc_atomic_sub.md)（`related`）：AscAtomicSub 与《ReadGmByPassDCache》的实质衔接是：SIMT asc_atomic_sub 是同一 GM 原子减；原子加提供逆操作对照，绕过 DCache 的读写和 AscDcci 共同落实 focal 明示的缓存一致性要求。
- [AscLoadDev](../../c_api/scalar_compute/asc_load_dev.md)（`related`）：“ReadGmByPassDCache”处理不经过DCache从GM地址读取数据。；“AscLoadDev”明确不经过DCache直接从Global Memory地址读取整型数据，避免多核操作未对齐Cache Line时的数据覆盖问题。。实质衔接：ReadGmByPassDCache 与 AscLoadDev 是同一旁路读取语义，配套写接口决定双向 GM 访问是否绕过 DCache。
- [AscStoreDev](../../c_api/scalar_compute/asc_store_dev.md)（`related`）：C++ bypass read 与 StoreDev 组成可见性验证。
- [DataCachePreload](../cache_control/data_cache_preload.md)（`related`）：DataCachePreload 与《ReadGmByPassDCache》的实质衔接是：DataCachePreload 是 GM 数据进入 DCache 的预取动作；清理失效、旁路读、DCCI 与一致性指南共同定义预取后可见性、失效和访问优化的完整契约。
- [WriteGmByPassDCache](write_gm_by_pass_d_cache_isasi.md)（`related`）：ReadGmByPassDCache 与 WriteGmByPassDCache 是绕过 Data Cache 的成对标量 GM 访问，一个读取、一个写入。
<!-- cannbot:related:end -->
