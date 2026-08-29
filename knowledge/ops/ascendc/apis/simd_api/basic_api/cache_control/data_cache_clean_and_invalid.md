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

- [Ascend950 DataCopy 写回 L2 驱逐丢对角线](../../../../runbooks/precision/ascend950_datacopy_l2.md)（`exemplifies`）：修复路线确认：CopyOut 改 `SetValue` 只写对角线 + 末尾一次 `DataCacheCleanAndInvalid` 后重跑全量 286/286 PASS，dense path 48/48、sparse path 238/238 三模式均 100% golden，`PRECISION_STATUS: PASS`（来源平台：Ascend950；证据等级: tool_observed）；当DMA向GM写入数据后，若Scalar需要读取该数据，需先调用本接口清除Data Cache中的旧缓存，否则可能读到过期数据。；运行手册给出 SetValue 与 DataCacheCleanAndInvalid 组合的 Ascend950 实测修复，API 卡说明清除旧 Data Cache line 以恢复 Scalar 侧 GM 可见性的调用合同，前者是后者在具体精度排障中的应用实例。
- [DataCacheCleanAndInvalid 无参调用导致编译失败](../../../../runbooks/compilation/datacache_clean_requires_tensor_target.md)（`exemplifies`）：当前 CANN 头文件暴露的是以 `LocalTensor<T>` 或 `GlobalTensor<T>` 为目标的函数重载，因此模板枚举解析和实参数量同时不满足契约。；函数原型提供基于GM地址和长度的清除方式。参数包含GM地址指针和数据长度。。运行手册的无参编译失败必须回到候选接口的显式目标范围契约，而不能臆造全缓存事件。
- [设置DCI编译选项来减少算子尾开销](../../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/dci_compile_option.md)（`explains`）：插入DCCI是一种额外的容错保证，如果开发者使用了* __gm__的方式改写GM内存，或者调用GlobalTensor.SetValue函数时，没有正确的调用DataCacheCleanAndInvalid接口来保证Cache一致性，编译框架自动插入DCCI恰好可以保证算子精度正常。；清除并失效Data Cache，确保Scalar单元通过Data Cache读取的GM数据与DMA单元直接写入GM的数据保持一致。。指南说明开启 no-dcache-flush 前必须手动承担 DCCI 的一致性职责，API 卡定义清除旧缓存与回刷可见性的接口作用，直接决定该编译优化能否安全启用。
- [GetValue](../data_structures/global_tensor/get_value.md)（`related`）：Scalar单元访问GM，首先会访问每个核内的Data Cache，因此存在Data Cache与GM的Cache一致性问题。；清除并失效Data Cache，确保Scalar单元通过Data Cache读取的GM数据与DMA单元直接写入GM的数据保持一致。当DMA向GM写入数据后，若Scalar需要读取该数据，需先调用本接口清除Data Cache中的旧缓存，否则可能读到过期数据。。GetValue 卡指出 Scalar 读 GM 会经过核内 Data Cache 并产生一致性风险，DataCacheCleanAndInvalid 卡给出 DMA 写后、Scalar 读前清除旧缓存的具体操作，构成读值前的缓存一致性处理链。
- [MatmulAllReduceAddRmsNorm A2 ACLNN 算子知识](../../../../operators/aclnn/transformer/mc2/matmul_all_reduce_add_rms_norm.md)（`related`）：融合算子用“AIV0 发布增长后的完成数，DCCI 清理/失效 cache line 后全 AIV 同步”广播 HCCL 完成前缀；缓存接口规定“当DMA向GM写入数据后，若Scalar需要读取该数据，需先调用本接口清除Data Cache中的旧缓存，否则可能读到过期数据。”，解释发布计数前后两次清理/失效的可见性目的。
- [SetValue](../data_structures/global_tensor/set_value.md)（`related`）：设置 GlobalTensor 指定偏移位置的元素值。操作先写入 DCache，需配合 DataCacheCleanAndInvalid 确保数据一致性。；清除并失效Data Cache，确保Scalar单元通过Data Cache读取的GM数据与DMA单元直接写入GM的数据保持一致。。SetValue 明确产生 DCache 写入，DataCacheCleanAndInvalid 提供写回并失效的可见性动作，联合阅读可闭合 GM 一致性处理。
<!-- cannbot:related:end -->
