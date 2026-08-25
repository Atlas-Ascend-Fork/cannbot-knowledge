---
type: API
title: GetValue
description: 获取GlobalTensor的相应偏移位置的值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/GetValue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetValue

获取GlobalTensor的相应偏移位置的值。

如图1所示，在AI Core内部，Scalar单元和DMA单元都可能对GM进行访问： - DMA搬运单元读写GM，数据通过DataCopy等接口在UB等Local Memory和GM间交互，没有Cache一致性问题。 - Scalar单元访问GM，首先会访问每个核内的Data Cache，因此存在Data Cache与GM的Cache一致性问题。 图1 DataCache内存层次示意图 DataCacheCleanAndInvalid接口用于解决上述一致性问题，其功能可以拆解为两部分： - Clean：将缓存中被修改过的数据（脏数据，Dirty Data）写回到GM中，避免数据丢失。 - Invalid： - 将指定地址范围的Cache Line标记为“无效”，使其从缓存中移除。 - 保证下一次访问这些内存地址时，会从GM重新加载数据，而不是使用可能过期的缓存数据。 该接口的典型使用场景如

本接口组包含 DataCacheCleanAndInvalid。

本接口属于 GlobalTensor 数据结构操作接口，用于访问和修改 GM 上的 Tensor 属性。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [AscendC DataCopy 标量参数模板推导失败](../../../../../runbooks/compilation/ascendc_datacopy.md)（`exemplifies`）：AscendC DataCopy 标量参数模板推导失败 与《GetValue》的实质衔接是：失败根因是把标量传给仅接收 LocalTensor 的 DataCopy；LocalTensor GetValue/SetValue 正是正文给出的逐元素修复。
- [GM SetValue 写回后 GetValue 读到旧值](../../../../../runbooks/precision/gm_setvalue_getvalue_reads_stale_within_kernel.md)（`exemplifies`）：故障在同一 kernel 后续用 GlobalTensor::GetValue 读取刚写的中间结果时复现；目标 API 是失效读路径本身。
- [arch35 GetValue/SetValue 标量bypass禁用](../../../../../runbooks/compilation/arch35_getvalue_setvalue_bypass.md)（`exemplifies`）：《arch35 GetValue/SetValue 标量bypass禁用》给出“在 arch35 RegBase 向量 kernel 中对标量输入（count==1）用 LocalTensor::GetValue/SetValue 做标量计算 bypass Compare+Select，Python ST 失败数远劣于 baseline（回退后恢复），scalar/vector API 混用有严重副作用，banned。”；该约束/探针可直接复现、解释或前置验证《GetValue》中的“获取GlobalTensor的相应偏移位置的值。”。
- [arch35 小 per-channel 输出读旧值判别与规避](../../../../../runbooks/compilation/arch35_per_channel.md)（`exemplifies`）：《arch35 小 per-channel 输出读旧值判别与规避》处理“arch35 上 DCCI 缓存不一致使 DataCopyPad 对小 per-channel [C] 输出不可靠、TQue GetValue(MTE2→scalar) 读到旧值；判别方法为先 V-launder(Duplicate 0.0f+Add) 到 TBuf 再 GetValue，并用 GlobalTensor::SetValue 直写 GM per-channel 结果。”。《GetValue》提供“获取GlobalTensor的相应偏移位置的值。”，其具体合同或探针直接接入arch35 小 per-channel 的 DCCI/Scalar 旧值机制、V-launder 与 SetValue 验证。
- [重复目标随机写丢失 — 在 UB 内按序合并后 DMA 写回](../../../../../runbooks/precision/repeated_overwrite_updates_need_ordered_ub_merge.md)（`exemplifies`）：本卡失败路线用 GlobalTensor::GetValue 逐元素读取 idx/upd；接口说明这是标量 GM 访问。
- [SetValue](set_value.md)（`related`）：《SetValue》的任务是“设置GlobalTensor指定偏移位置的元素值，操作先写入DCache，需配合DataCacheCleanAndInvalid确保一致性。”。《GetValue》具体提供“获取GlobalTensor的相应偏移位置的值。”，它直接用于GlobalTensor 标量写入后的 DCache 可见性与 GetValue 验证。
- [operator](operator_call.md)（`same_topic`）：GetValue is the explicit rvalue operation equivalent to using GlobalTensor::operator() on the right-hand side.
<!-- cannbot:related:end -->
