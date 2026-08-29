---
type: API
title: SetValue
description: 设置GlobalTensor指定偏移位置的元素值，操作先写入DCache，需配合DataCacheCleanAndInvalid确保一致性。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/SetValue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetValue

设置 GlobalTensor 指定偏移位置的元素值。操作先写入 DCache，需配合 DataCacheCleanAndInvalid 确保数据一致性。参数 offset 为偏移量，value 为设置的值。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [GM SetValue 写回后 GetValue 读到旧值](../../../../../runbooks/precision/gm_setvalue_getvalue_reads_stale_within_kernel.md)（`exemplifies`）：“关键点：ProcessR 用 `CopyOutArray(rOutLocal, rOutGm_, n_)`（即 `rOutGm_.SetValue(...)`）把 r_out 写回 GM，ProcessC 同样把 c_out 写回 GM；ProcessU 随后用 `rOutGm_.GetValue(i)` 与 `CopyInArray(cOutLocal, cOutGm_, m_)` 再从 GM 读回。读回的值并未反映本 Kernel 刚写入的更新。”复现同 Kernel 写后读旧值，而“设置 GlobalTensor 指定偏移位置的元素值。操作先写入 DCache，需配合 DataCacheCleanAndInvalid 确保数据一致性。”给出 SetValue 的 DCache 一致性合同；runbook 直接示范违反该合同的故障。
- [DataCacheCleanAndInvalid](../../cache_control/data_cache_clean_and_invalid.md)（`related`）：设置 GlobalTensor 指定偏移位置的元素值。操作先写入 DCache，需配合 DataCacheCleanAndInvalid 确保数据一致性。；清除并失效Data Cache，确保Scalar单元通过Data Cache读取的GM数据与DMA单元直接写入GM的数据保持一致。。SetValue 明确产生 DCache 写入，DataCacheCleanAndInvalid 提供写回并失效的可见性动作，联合阅读可闭合 GM 一致性处理。
- [operator](operator_call.md)（`related`）：返回值为指定索引位置的 PrimType 类型引用，用于左值相当于 SetValue，用于右值相当于 GetValue。；设置 GlobalTensor 指定偏移位置的元素值。操作先写入 DCache，需配合 DataCacheCleanAndInvalid 确保数据一致性。。GlobalTensor operator() 卡明确左值语境等价于 SetValue，SetValue 卡说明指定偏移写入及 DCache 一致性要求，二者连接运算符重载与显式写接口。
<!-- cannbot:related:end -->
