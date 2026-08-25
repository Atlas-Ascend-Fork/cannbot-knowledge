---
type: API
title: WriteGmByPassDCache
description: 不经过DCache向GM地址写入数据，可避免多核Cache Line数据覆盖问题。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/scalar_compute/WriteGmByPassDCache_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# WriteGmByPassDCache

头文件路径为："basic_api/kernel_operator_scalar_intf.h"。

不经过DCache向GM地址上写数据。

> [!CAUTION]注意
> 针对NPU架构2201，接口能否将value成功写入GM还与目标地址addr有关，具体

使用场景
- 当多个核写入的数据落在同一条Cache Line内时，经过DCache的读写将以64B为粒度，可能引发多核数据随机覆盖问题（参考DataCacheCleanAndInvalid调用示例3）。使用该接口不经过DCache直接按操作数大小写GM，可避免此问题。
- 经过DCache写GM时可能导致多核间的数据不一致问题（详细原因

由于WriteGmByPassDCache接口向GM写数据时不经过DCache，因此开发者需要考虑如下场景

参数：T: 操作数的数据类型。；addr(输入): 目标GM地址。；value(输入): 待写入目标数据。

支持数据类型：支持的数据类型为int8_t、uint8_t、int16_t、uint16_t、int32_t、uint32_t、int64_t、uint64_t。

约束：针对NPU架构2201，接口是否执行写入取决于目标地址addr在当前128字节对齐区间内的偏移。令，当时，写入生效；当时，不执行写入，目标地址中的数据保持原值。即仅当目标地址位于每个128字节对齐区间的前32字节时，接口才执行写入。

设接口调用前后的目标地址数据分别为和，则

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [DataCacheCleanAndInvalid 无参调用导致编译失败](../../../../runbooks/compilation/datacache_clean_requires_tensor_target.md)（`exemplifies`）：DataCacheCleanAndInvalid 无参调用导致编译失败 与《WriteGmByPassDCache》的实质衔接是：编译失败源于把 DataCacheCleanAndInvalid 臆造成无参全缓存调用；真实 Tensor 目标 API、preload/cache 总览、L2 hint 和 DCI 写回故障说明缓存操作必须绑定对象与执行边界。
- [AscAtomicSub](../../c_api/scalar_compute/asc_atomic_sub.md)（`related`）：AscAtomicSub 与《WriteGmByPassDCache》的实质衔接是：SIMT asc_atomic_sub 是同一 GM 原子减；原子加提供逆操作对照，绕过 DCache 的读写和 AscDcci 共同落实 focal 明示的缓存一致性要求。
- [AscDcci](../../c_api/cache_ctrl/asc_dcci.md)（`related`）：AscDcci 是 C API 的数据缓存清理/失效入口，可与 bypass 写对照确定是维护已有缓存行还是避免写入 DCache。
- [DataCacheCleanAndInvalid](../cache_control/data_cache_clean_and_invalid.md)（`related`）：ByPass DCache 写 GM 会绕过普通缓存路径，需要结合 clean/invalid 决定后续观察到的数据一致性。
- [ReadGmByPassDCache](read_gm_by_pass_d_cache_isasi.md)（`related`）：ReadGmByPassDCache 与 WriteGmByPassDCache 是绕过 Data Cache 的成对标量 GM 访问，一个读取、一个写入。
- [标量计算](scalar_compute.md)（`related`）：标量计算总览收录 bypass DCache 的 GM 读写，并将其与转换、位操作等 Scalar 能力区分。
- [AscStoreDev](../../c_api/scalar_compute/asc_store_dev.md)（`same_topic`）：WriteGmByPassDCache 与 AscStoreDev 都绕过 DCache 向 GM 写入单个标量，以规避多核共享 Cache Line 的覆盖；平台与地址约束不同，但核心写入语义一致。
<!-- cannbot:related:end -->
