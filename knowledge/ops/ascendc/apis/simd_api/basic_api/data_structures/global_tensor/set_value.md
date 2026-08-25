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

- [AscendC DataCopy 标量参数模板推导失败](../../../../../runbooks/compilation/ascendc_datacopy.md)（`exemplifies`）：AscendC DataCopy 标量参数模板推导失败 与《SetValue》的实质衔接是：失败根因是把标量传给仅接收 LocalTensor 的 DataCopy；LocalTensor GetValue/SetValue 正是正文给出的逐元素修复。
- [GM SetValue 写回后 GetValue 读到旧值](../../../../../runbooks/precision/gm_setvalue_getvalue_reads_stale_within_kernel.md)（`exemplifies`）：《SetValue》的任务是“设置GlobalTensor指定偏移位置的元素值，操作先写入DCache，需配合DataCacheCleanAndInvalid确保一致性。”。《GM SetValue 写回后 GetValue 读到旧值》具体提供“同一 Kernel 内用 SetValue 把中间结果写回 GM，后续 GetValue 读回的不是刚写入的新值而是更新前旧值，导致依赖该中间值的下游计算出现系统性小偏差。”，它直接用于GlobalTensor 标量写入后的 DCache 可见性与 GetValue 验证。
- [arch35 GetValue/SetValue 标量bypass禁用](../../../../../runbooks/compilation/arch35_getvalue_setvalue_bypass.md)（`exemplifies`）：《SetValue》的任务是“设置GlobalTensor指定偏移位置的元素值，操作先写入DCache，需配合DataCacheCleanAndInvalid确保一致性。”。《arch35 GetValue/SetValue 标量bypass禁用》具体提供“在 arch35 RegBase 向量 kernel 中对标量输入（count==1）用 LocalTensor::GetValue/SetValue 做标量计算 bypass Compare+Select，Python ST 失败数远劣于 baseline（回退后恢复），scalar/vector API 混用有严重副作用，banned。”，它直接用于GlobalTensor 标量写入后的 DCache 可见性与 GetValue 验证。
- [arch35 小 per-channel 输出读旧值判别与规避](../../../../../runbooks/compilation/arch35_per_channel.md)（`exemplifies`）：《arch35 小 per-channel 输出读旧值判别与规避》处理“arch35 上 DCCI 缓存不一致使 DataCopyPad 对小 per-channel [C] 输出不可靠、TQue GetValue(MTE2→scalar) 读到旧值；判别方法为先 V-launder(Duplicate 0.0f+Add) 到 TBuf 再 GetValue，并用 GlobalTensor::SetValue 直写 GM per-channel 结果。”。《SetValue》提供“设置GlobalTensor指定偏移位置的元素值，操作先写入DCache，需配合DataCacheCleanAndInvalid确保一致性。”，其具体合同或探针直接接入arch35 小 per-channel 的 DCCI/Scalar 旧值机制、V-launder 与 SetValue 验证。
- [重复目标随机写丢失 — 在 UB 内按序合并后 DMA 写回](../../../../../runbooks/precision/repeated_overwrite_updates_need_ordered_ub_merge.md)（`exemplifies`）：不确定性直接出现在对重复目标连续调用 GlobalTensor::SetValue。
- [Scalar读写数据](../../../../../guides/technical_appendix/concepts_and_terms/memory_access/scalar_read_write.md)（`explains`）：《SetValue》的任务是“设置GlobalTensor指定偏移位置的元素值，操作先写入DCache，需配合DataCacheCleanAndInvalid确保一致性。”。《Scalar读写数据》具体提供“Scalar计算单元仅支持读写Global Memory和Unified Buffer，介绍其读写方式及同步机制。”，它直接用于GlobalTensor 标量写入后的 DCache 可见性与 GetValue 验证。
- [DataCacheCleanAndInvalid](../../cache_control/data_cache_clean_and_invalid.md)（`related`）：《SetValue》的任务是“设置GlobalTensor指定偏移位置的元素值，操作先写入DCache，需配合DataCacheCleanAndInvalid确保一致性。”。《DataCacheCleanAndInvalid》具体提供“解决Data Cache与GM一致性问题，将脏数据写回GM并将指定Cache Line标记为无效，确保下次访问从GM重新加载。”，它直接用于GlobalTensor 标量写入后的 DCache 可见性与 GetValue 验证。
- [GetValue](get_value.md)（`related`）：《SetValue》的任务是“设置GlobalTensor指定偏移位置的元素值，操作先写入DCache，需配合DataCacheCleanAndInvalid确保一致性。”。《GetValue》具体提供“获取GlobalTensor的相应偏移位置的值。”，它直接用于GlobalTensor 标量写入后的 DCache 可见性与 GetValue 验证。
- [SetL2CacheHint](set_l2_cache_hint.md)（`related`）：《SetValue》的任务是“设置GlobalTensor指定偏移位置的元素值，操作先写入DCache，需配合DataCacheCleanAndInvalid确保一致性。”。《SetL2CacheHint》具体提供“设置GlobalTensor是否启用L2 Cache，默认启用L2 Cache。”，它直接用于GlobalTensor 标量写入后的 DCache 可见性与 GetValue 验证。
<!-- cannbot:related:end -->
