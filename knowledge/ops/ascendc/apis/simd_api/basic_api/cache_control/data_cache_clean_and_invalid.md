---
type: API
title: DataCacheCleanAndInvalid
description: 解决Data Cache与GM一致性问题，将脏数据写回GM并将指定Cache Line标记为无效，确保下次访问从GM重新加载。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cache_control/DataCacheCleanAndInvalid.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# DataCacheCleanAndInvalid

清除并失效Data Cache，确保Scalar单元通过Data Cache读取的GM数据与DMA单元直接写入GM的数据保持一致。当DMA向GM写入数据后，若Scalar需要读取该数据，需先调用本接口清除Data Cache中的旧缓存，否则可能读到过期数据。

函数原型提供基于GM地址和长度的清除方式。参数包含GM地址指针和数据长度。约束：仅在Scalar单元访问GM时需要；DMA搬运不涉及Cache一致性问题。头文件：basic_api/kernel_operator_cache_intf.h。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 DataCopy 写回 L2 驱逐丢对角线](../../../../runbooks/precision/ascend950_datacopy_l2.md)（`exemplifies`）：该接口负责把 dirty cache line 写回 GM 并失效；本卡证明末尾一次调用无法挽回容量驱逐前已丢失的 DataCopy dirty line。
- [DataCacheCleanAndInvalid 无参调用导致编译失败](../../../../runbooks/compilation/datacache_clean_requires_tensor_target.md)（`exemplifies`）：DataCacheCleanAndInvalid 无参调用导致编译失败 与《DataCacheCleanAndInvalid》的实质衔接是：编译失败源于把 DataCacheCleanAndInvalid 臆造成无参全缓存调用；真实 Tensor 目标 API、preload/cache 总览、L2 hint 和 DCI 写回故障说明缓存操作必须绑定对象与执行边界。
- [缓存一致性](../../../../guides/programming_guide/advanced_programming/memory_model/cache_coherence.md)（`explains`）：一致性指南解释各存储层和显式维护时机，为区分 clean、invalid 与 barrier 提供机制依据。
- [设置DCI编译选项来减少算子尾开销](../../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/dci_compile_option.md)（`explains`）：开启 --cce-no-dcache-flush 后编译器不再用尾部 DCCI 兜底，所有 *GM/SetValue 写必须自行 DataCacheCleanAndInvalid 回刷；API 卡给出该显式一致性动作。
- [AscDcci](../../c_api/cache_ctrl/asc_dcci.md)（`related`）：AscDcci 与《DataCacheCleanAndInvalid》的实质衔接是：AscDcci 的 single/entire 变体与 C++ DataCacheCleanAndInvalid 操作同一 DCache；缓存概述、L2 驱逐故障和编译选项提供验证与尾开销决策。
- [DataCachePreload](data_cache_preload.md)（`related`）：DataCachePreload 与《DataCacheCleanAndInvalid》的实质衔接是：DataCachePreload 是 GM 数据进入 DCache 的预取动作；清理失效、旁路读、DCCI 与一致性指南共同定义预取后可见性、失效和访问优化的完整契约。
- [SetValue](../data_structures/global_tensor/set_value.md)（`related`）：《SetValue》的任务是“设置GlobalTensor指定偏移位置的元素值，操作先写入DCache，需配合DataCacheCleanAndInvalid确保一致性。”。《DataCacheCleanAndInvalid》具体提供“解决Data Cache与GM一致性问题，将脏数据写回GM并将指定Cache Line标记为无效，确保下次访问从GM重新加载。”，它直接用于GlobalTensor 标量写入后的 DCache 可见性与 GetValue 验证。
- [WriteGmByPassDCache](../scalar_compute/write_gm_by_pass_d_cache_isasi.md)（`related`）：ByPass DCache 写 GM 会绕过普通缓存路径，需要结合 clean/invalid 决定后续观察到的数据一致性。
- [系统缓存概述（缓存控制）](system_cache_overview.md)（`same_topic`）：系统缓存概述（缓存控制） 与《DataCacheCleanAndInvalid》的实质衔接是：系统缓存由 DCache/ICache 预取、DCache 清理失效、L2 hint 与 DCCI 共同控制；一致性错误卡给出清理接口必须指定目标 tensor 的调用约束。
- [缓存控制](cache_control.md)（`same_topic`）：缓存控制总页说明 clean、invalid、preload 的作用范围和组合，是本接口的机制入口。
<!-- cannbot:related:end -->
