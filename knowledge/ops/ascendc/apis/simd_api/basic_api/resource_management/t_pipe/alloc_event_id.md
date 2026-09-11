---
type: API
title: AllocEventID
description: 用于申请HardEvent（硬件类型同步事件）的TEventID，必须与ReleaseEventID搭配使用，调用后占用TEventID直至释放。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.memory_management
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/AllocEventID.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- '910'
- kirin_x90
- kirin_9030
source_headers:
- include/basic_api/kernel_tpipe.h
---

# AllocEventID<a name="ZH-CN_TOPIC_0000001791611817"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_tpipe.h"`。

用于申请HardEvent（硬件类型同步事件）的TEventID，必须与[ReleaseEventID](release_event_id.md)搭配使用，调用该接口后，会占用申请的TEventID，直至调用ReleaseEventID释放。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
template <HardEvent evt>
__aicore__ inline TEventID AllocEventID()
```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  模板参数说明

<a name="table193329316393"></a>
<table><thead align="left"><tr id="row123331131153919"><th class="cellrowborder" valign="top" width="16.29%" id="mcps1.2.3.1.1"><p id="p8333133153913"><a name="p8333133153913"></a><a name="p8333133153913"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="83.71%" id="mcps1.2.3.1.2"><p id="p833353113393"><a name="p833353113393"></a><a name="p833353113393"></a>描述</p>
</th>
</tr>
</thead>
<tbody><tr id="row11660173845017"><td class="cellrowborder" valign="top" width="16.29%" headers="mcps1.2.3.1.1 "><p id="p4571114971214"><a name="p4571114971214"></a><a name="p4571114971214"></a>evt</p>
</td>
<td class="cellrowborder" valign="top" width="83.71%" headers="mcps1.2.3.1.2 "><p id="p15571184910124"><a name="p15571184910124"></a><a name="p15571184910124"></a>HardEvent硬件同步类型。该类型的具体说明请参考<a href="../../sync_control/intra_core_sync/set_flag_wait_flag_isasi.md">SetFlag/WaitFlag(ISASI)</a>中同步类型的说明。</p>
</td>
</tr>
</tbody>
</table>

## 约束说明<a name="section633mcpsimp"></a>

TEventID有数量限制，使用结束后应该立刻调用ReleaseEventID释放，防止TEventID耗尽。

## 返回值说明<a name="section640mcpsimp"></a>

TEventID

## 调用示例<a name="section642mcpsimp"></a>

```cpp
AscendC::TEventID eventID = GetTPipePtr()->AllocEventID<AscendC::HardEvent::V_S>(); //需要插入scalar等vector的同步，申请对应的HardEvent的ID
AscendC::SetFlag<AscendC::HardEvent::V_S>(eventID);
......
......
......
AscendC::WaitFlag<AscendC::HardEvent::V_S>(eventID);
GetTPipePtr()->ReleaseEventID<AscendC::HardEvent::V_S>(eventID); //释放scalar等vector的同步HardEvent的ID
......
```


<!-- cannbot:related:start -->
## 相关

- [FetchEventID](fetch_event_id.md)（`related`）：“相比于AllocEventID，FetchEventID适用于临时使用ID的场景，获取ID后，不会对ID进行占用。”给出不占用路线；“用于申请HardEvent（硬件类型同步事件）的TEventID，必须与ReleaseEventID搭配使用，调用该接口后，会占用申请的TEventID，直至调用ReleaseEventID释放。”给出复杂同步需要独占 ID 时的替代生命周期。
- [ReleaseEventID](release_event_id.md)（`related`）：用于申请HardEvent（硬件类型同步事件）的TEventID，必须与ReleaseEventID搭配使用，调用该接口后，会占用申请的TEventID，直至调用ReleaseEventID释放。；约束：AllocEventID、ReleaseEventID需成对出现，ReleaseEventID传入的TEventID需由对应的AllocEventID申请而来。。AllocEventID 产生并占用 TEventID，ReleaseEventID 消费该句柄并结束占用；申请与释放是同一资源生命周期中的相反步骤，而不是同一接口主题的模式变体。
- [SetFlag/WaitFlag](../../sync_control/intra_core_sync/set_flag_wait_flag.md)（`related`）：参数：id(输入): 事件ID，由用户自己指定，推荐通过AllocEventID或者FetchEventID来获取。定义如下： using TEventID = int8_t;。；用于申请HardEvent（硬件类型同步事件）的TEventID，必须与ReleaseEventID搭配使用，调用该接口后，会占用申请的TEventID，直至调用ReleaseEventID释放。。SetFlag/WaitFlag 消费 TEventID，AllocEventID 提供受生命周期管理的硬件事件 ID，闭合同步事件获取与使用。
- [SetFlag/WaitFlag](../../sync_control/intra_core_sync/set_flag_wait_flag_isasi.md)（`related`）：- 在采用TPipe-TQue框架编程范式时，eventID需要通过AllocEventID或者FetchEventID来获取。；用于申请HardEvent（硬件类型同步事件）的TEventID，必须与ReleaseEventID搭配使用，调用该接口后，会占用申请的TEventID，直至调用ReleaseEventID释放。。同步卡要求从 TPipe 获取 eventID，AllocEventID 提供带申请和释放生命周期的 HardEvent ID。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 37 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [InplaceTril 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/inplace_tril_950.md)（`related`）：算子声明的固定版本源码包含对 `AllocEventID(...)` 的直接调用（第 124 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/triu/op_kernel/arch35/split_all.h#L124)
- [SwigluGroupQuant 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/swiglu_group_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `AllocEventID(...)` 的直接调用（第 234 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/swiglu_group_quant/op_kernel/arch35/swiglu_dynamic_group_quant_hifp8.h#L234)
- [FlashAttentionScore 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attention_score_950.md)（`related`）：算子声明的固定版本源码包含对 `AllocEventID(...)` 的直接调用（第 773 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/common/op_kernel/arch35/flash_attention_noquant_block_vec_base.h#L773)
- [InplaceTriu 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/inplace_triu_950.md)（`related`）：算子声明的固定版本源码包含对 `AllocEventID(...)` 的直接调用（第 124 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/triu/op_kernel/arch35/split_all.h#L124)
- [SwigluGroupQuantGrad 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/swiglu_group_quant_grad_950.md)（`related`）：算子声明的固定版本源码包含对 `AllocEventID(...)` 的直接调用（第 374 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/swiglu_group_quant_grad/op_kernel/swiglu_group_quant_grad.h#L374)
- [FlashAttentionVarLenScore 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attention_var_len_score_950.md)（`related`）：算子声明的固定版本源码包含对 `AllocEventID(...)` 的直接调用（第 596 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/common/op_kernel/arch35/flash_attention_score_block_vec_base.h#L596)
- [Tril 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/tril_950.md)（`related`）：算子声明的固定版本源码包含对 `AllocEventID(...)` 的直接调用（第 124 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/triu/op_kernel/arch35/split_all.h#L124)
- [DeformableConv2d A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/conv/deformable_conv2d.md)（`related`）：算子声明的固定版本源码包含对 `AllocEventID(...)` 的直接调用（第 441 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/conv/deformable_conv2d/op_kernel/deformable_conv2d_base.h#L441)
- [IncreFlashAttention A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/incre_flash_attention.md)（`related`）：算子声明的固定版本源码包含对 `AllocEventID(...)` 的直接调用（第 717 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/incre_flash_attention/op_kernel/ifa_public_define.h#L717)
- [Triu 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/triu_950.md)（`related`）：算子声明的固定版本源码包含对 `AllocEventID(...)` 的直接调用（第 124 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/triu/op_kernel/arch35/split_all.h#L124)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
