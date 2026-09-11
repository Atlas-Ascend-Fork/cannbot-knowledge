---
type: API
title: ReleaseEventID
description: 用于释放HardEvent硬件同步事件的TEventID，通常与AllocEventID搭配使用。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.memory_management
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/ReleaseEventID.md
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

# ReleaseEventID<a name="ZH-CN_TOPIC_0000001744571864"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_tpipe.h"`。

用于释放HardEvent（硬件类型同步事件）的TEventID，通常与[AllocEventID](alloc_event_id.md)搭配使用。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
template <HardEvent evt>
__aicore__ inline void ReleaseEventID(TEventID id)
```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  模板参数说明

<a name="table58993346461"></a>
<table><thead align="left"><tr id="row88991534124617"><th class="cellrowborder" valign="top" width="12.23%" id="mcps1.2.3.1.1"><p id="p5899163484616"><a name="p5899163484616"></a><a name="p5899163484616"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="87.77000000000001%" id="mcps1.2.3.1.2"><p id="p1889953419469"><a name="p1889953419469"></a><a name="p1889953419469"></a>描述</p>
</th>
</tr>
</thead>
<tbody><tr id="row18991634144619"><td class="cellrowborder" valign="top" width="12.23%" headers="mcps1.2.3.1.1 "><p id="p118996346463"><a name="p118996346463"></a><a name="p118996346463"></a>evt</p>
</td>
<td class="cellrowborder" valign="top" width="87.77000000000001%" headers="mcps1.2.3.1.2 "><p id="p1389943411468"><a name="p1389943411468"></a><a name="p1389943411468"></a>HardEvent硬件同步类型。该类型的具体说明请参考<a href="../../sync_control/intra_core_sync/set_flag_wait_flag_isasi.md">SetFlag/WaitFlag(ISASI)</a>中同步类型的说明。</p>
</td>
</tr>
</tbody>
</table>

**表2**  参数说明

<a name="table193329316393"></a>
<table><thead align="left"><tr id="row123331131153919"><th class="cellrowborder" valign="top" width="12.36%" id="mcps1.2.4.1.1"><p id="p8333133153913"><a name="p8333133153913"></a><a name="p8333133153913"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="12.379999999999999%" id="mcps1.2.4.1.2"><p id="p518118718459"><a name="p518118718459"></a><a name="p518118718459"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="75.26%" id="mcps1.2.4.1.3"><p id="p833353113393"><a name="p833353113393"></a><a name="p833353113393"></a>描述</p>
</th>
</tr>
</thead>
<tbody><tr id="row11660173845017"><td class="cellrowborder" valign="top" width="12.36%" headers="mcps1.2.4.1.1 "><p id="p18393187172718"><a name="p18393187172718"></a><a name="p18393187172718"></a>id</p>
</td>
<td class="cellrowborder" valign="top" width="12.379999999999999%" headers="mcps1.2.4.1.2 "><p id="p1461163910269"><a name="p1461163910269"></a><a name="p1461163910269"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="75.26%" headers="mcps1.2.4.1.3 "><p id="p143308311967"><a name="p143308311967"></a><a name="p143308311967"></a>TEventID类型，调用<a href="alloc_event_id.md">AllocEventID</a>申请获得的TEventID。</p>
</td>
</tr>
</tbody>
</table>

## 约束说明<a name="section633mcpsimp"></a>

AllocEventID、ReleaseEventID需成对出现，ReleaseEventID传入的TEventID需由对应的AllocEventID申请而来。

## 返回值说明<a name="section640mcpsimp"></a>

无

## 调用示例<a name="section882216131071"></a>

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

- [AllocEventID](alloc_event_id.md)（`related`）：用于申请HardEvent（硬件类型同步事件）的TEventID，必须与ReleaseEventID搭配使用，调用该接口后，会占用申请的TEventID，直至调用ReleaseEventID释放。；约束：AllocEventID、ReleaseEventID需成对出现，ReleaseEventID传入的TEventID需由对应的AllocEventID申请而来。。AllocEventID 产生并占用 TEventID，ReleaseEventID 消费该句柄并结束占用；申请与释放是同一资源生命周期中的相反步骤，而不是同一接口主题的模式变体。
- [FetchEventID](fetch_event_id.md)（`related`）：“相比于AllocEventID，FetchEventID适用于临时使用ID的场景，获取ID后，不会对ID进行占用。”说明 Fetch 路线没有释放生命周期；“AllocEventID、ReleaseEventID需成对出现，ReleaseEventID传入的TEventID需由对应的AllocEventID申请而来。”界定改用独占 ID 后必须履行的释放合同。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 37 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [InplaceTril 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/inplace_tril_950.md)（`related`）：算子声明的固定版本源码包含对 `ReleaseEventID(...)` 的直接调用（第 133 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/triu/op_kernel/arch35/split_all.h#L133)
- [SwigluGroupQuant 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/swiglu_group_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `ReleaseEventID(...)` 的直接调用（第 237 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/swiglu_group_quant/op_kernel/arch35/swiglu_dynamic_group_quant_hifp8.h#L237)
- [FlashAttentionScore 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attention_score_950.md)（`related`）：算子声明的固定版本源码包含对 `ReleaseEventID(...)` 的直接调用（第 156 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/common/op_kernel/buffer.h#L156)
- [InplaceTriu 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/inplace_triu_950.md)（`related`）：算子声明的固定版本源码包含对 `ReleaseEventID(...)` 的直接调用（第 133 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/triu/op_kernel/arch35/split_all.h#L133)
- [SwigluGroupQuantGrad 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/swiglu_group_quant_grad_950.md)（`related`）：算子声明的固定版本源码包含对 `ReleaseEventID(...)` 的直接调用（第 386 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/swiglu_group_quant_grad/op_kernel/swiglu_group_quant_grad.h#L386)
- [FlashAttn 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attn_950.md)（`related`）：算子声明的固定版本源码包含对 `ReleaseEventID(...)` 的直接调用（第 1187 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attn/op_kernel/arch35/flash_attn_block_vec_noquant_gqa.h#L1187)
- [Tril 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/tril_950.md)（`related`）：算子声明的固定版本源码包含对 `ReleaseEventID(...)` 的直接调用（第 133 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/triu/op_kernel/arch35/split_all.h#L133)
- [DeformableConv2d A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/conv/deformable_conv2d.md)（`related`）：算子声明的固定版本源码包含对 `ReleaseEventID(...)` 的直接调用（第 452 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/conv/deformable_conv2d/op_kernel/deformable_conv2d_base.h#L452)
- [IncreFlashAttention A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/incre_flash_attention.md)（`related`）：算子声明的固定版本源码包含对 `ReleaseEventID(...)` 的直接调用（第 781 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/incre_flash_attention/op_kernel/ifa_public_define.h#L781)
- [Triu 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/triu_950.md)（`related`）：算子声明的固定版本源码包含对 `ReleaseEventID(...)` 的直接调用（第 133 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/triu/op_kernel/arch35/split_all.h#L133)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
