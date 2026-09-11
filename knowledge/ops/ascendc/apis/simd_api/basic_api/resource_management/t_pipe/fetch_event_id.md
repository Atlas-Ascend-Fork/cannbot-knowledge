---
type: API
title: FetchEventID
description: 根据HardEvent获取相应可用的TEventID，此接口不会申请TEventID，仅提供可用的TEventID。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.memory_management
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/FetchEventID.md
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

# FetchEventID<a name="ZH-CN_TOPIC_0000001791531573"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_tpipe.h"`。

根据HardEvent（硬件类型的同步事件）获取相应可用的TEventID，此接口不会申请TEventID，仅提供可用的TEventID。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
template <HardEvent evt>
__aicore__ inline TEventID FetchEventID()
__aicore__ inline TEventID FetchEventID(HardEvent evt)
```

## 参数说明<a name="section622mcpsimp"></a>

<a name="table193329316393"></a>
<table><thead align="left"><tr id="row123331131153919"><th class="cellrowborder" valign="top" width="12.36%" id="mcps1.1.4.1.1"><p id="p8333133153913"><a name="p8333133153913"></a><a name="p8333133153913"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="12.379999999999999%" id="mcps1.1.4.1.2"><p id="p518118718459"><a name="p518118718459"></a><a name="p518118718459"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="75.26%" id="mcps1.1.4.1.3"><p id="p833353113393"><a name="p833353113393"></a><a name="p833353113393"></a>含义</p>
</th>
</tr>
</thead>
<tbody><tr id="row11660173845017"><td class="cellrowborder" valign="top" width="12.36%" headers="mcps1.1.4.1.1 "><p id="p143161011192917"><a name="p143161011192917"></a><a name="p143161011192917"></a>evt</p>
</td>
<td class="cellrowborder" valign="top" width="12.379999999999999%" headers="mcps1.1.4.1.2 "><p id="p9331531865"><a name="p9331531865"></a><a name="p9331531865"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="75.26%" headers="mcps1.1.4.1.3 "><p id="p143308311967"><a name="p143308311967"></a><a name="p143308311967"></a>HardEvent类型，硬件同步类型。</p>
<p id="p15571184910124"><a name="p15571184910124"></a><a name="p15571184910124"></a>该类型的具体说明请参考<a href="../../sync_control/intra_core_sync/set_flag_wait_flag_isasi.md">SetFlag/WaitFlag(ISASI)</a>中同步类型的说明。</p>
</td>
</tr>
</tbody>
</table>

## 约束说明<a name="section633mcpsimp"></a>

相比于[AllocEventID](alloc_event_id.md)，FetchEventID适用于临时使用ID的场景，获取ID后，不会对ID进行占用。在一些复杂的使用场景下，需要开发者自行保证使用正确。比如相同流水连续调用SetFlag/WaitFlag，如果两次传入的ID都是使用FetchEventID获取的，因为两者ID相同会出现程序卡死等未定义行为，这时推荐用户使用AllocEventID。

## 返回值说明<a name="section640mcpsimp"></a>

TEventID

## 调用示例<a name="section6191129670"></a>

```cpp
AscendC::TEventID eventIdVToS = GetTPipePtr()->FetchEventID(AscendC::HardEvent::V_S); //需要插scalar等vector的同步，申请对应的HardEvent的ID
AscendC::SetFlag<AscendC::HardEvent::V_S>(eventIdVToS);
AscendC::WaitFlag<AscendC::HardEvent::V_S>(eventIdVToS);
```


<!-- cannbot:related:start -->
## 相关

- [GetTPipePtr 错加 AscendC 命名空间导致编译失败](../../../../../runbooks/compilation/gettpipeptr_is_global_function.md)（`exemplifies`）：“未改 `AscendC::HardEvent`、`FetchEventID` 或同步事件种类，因为报错只指向函数名的命名空间查找；”说明修复后事件调用合同保持不变；“根据HardEvent（硬件类型的同步事件）获取相应可用的TEventID，此接口不会申请TEventID，仅提供可用的TEventID。”定义该成员调用的语义。
- [探针末尾 MTE2_S/MTE3_S 同步不可由 stream sync 替代](../../../../../runbooks/compilation/mte2_s_mte3_s_stream_sync.md)（`exemplifies`）：“- API 路径：`PipeBarrier<PIPE_MTE2｜PIPE_MTE3>`；`GetTPipePtr()->FetchEventID(HardEvent::MTE2_S｜MTE3_S)`；`SetFlag`/`WaitFlag`；Host 侧 `aclrtSynchronizeStream`。”与“根据HardEvent（硬件类型的同步事件）获取相应可用的TEventID，此接口不会申请TEventID，仅提供可用的TEventID。”提供双方正文证据。排障卡在 MTE2_S/MTE3_S 同步序列中实际调用 FetchEventID，API 卡说明它按 HardEvent 返回但不占用 TEventID，支撑该事件配对的资源判断。
- [AllocEventID](alloc_event_id.md)（`related`）：“相比于AllocEventID，FetchEventID适用于临时使用ID的场景，获取ID后，不会对ID进行占用。”给出不占用路线；“用于申请HardEvent（硬件类型同步事件）的TEventID，必须与ReleaseEventID搭配使用，调用该接口后，会占用申请的TEventID，直至调用ReleaseEventID释放。”给出复杂同步需要独占 ID 时的替代生命周期。
- [DequantBias A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/quant/dequant_bias.md)（`related`）：“event_t eventMTE2V = static_cast<event_t>(GetTPipePtr()->FetchEventID(HardEvent::MTE2_V));”给出 DequantBias 的 MTE2→V 临时事件取得方式；“此接口不会申请TEventID，仅提供可用的TEventID。”提示该调用不占用事件 ID，连续复用时需由实现保证安全。
- [ReleaseEventID](release_event_id.md)（`related`）：“相比于AllocEventID，FetchEventID适用于临时使用ID的场景，获取ID后，不会对ID进行占用。”说明 Fetch 路线没有释放生命周期；“AllocEventID、ReleaseEventID需成对出现，ReleaseEventID传入的TEventID需由对应的AllocEventID申请而来。”界定改用独占 ID 后必须履行的释放合同。
- [SetFlag/WaitFlag](../../sync_control/intra_core_sync/set_flag_wait_flag_isasi.md)（`related`）：- 在采用TPipe-TQue框架编程范式时，eventID需要通过AllocEventID或者FetchEventID来获取。；根据HardEvent（硬件类型的同步事件）获取相应可用的TEventID，此接口不会申请TEventID，仅提供可用的TEventID。。同步卡列出 FetchEventID 获取 eventID，目标卡说明它只返回可用 ID 而不占用申请槽位。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 208 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [UpsampleBicubic2dAAGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bicubic_2d_aa_grad.md)（`related`）：算子声明的固定版本源码包含对 `FetchEventID(...)` 的直接调用（第 627 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bicubic2d_aa_grad/op_kernel/upsample_bicubic2d_aa_grad.h#L627)
- [Cat 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/cat_950.md)（`related`）：算子声明的固定版本源码包含对 `FetchEventID(...)` 的直接调用（第 355 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/concat/op_kernel/arch35/one_axis_concat_no_align_diff_shape.h#L355)
- [ClippedSwiglu 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/clipped_swiglu_950.md)（`related`）：算子声明的固定版本源码包含对 `FetchEventID(...)` 的直接调用（第 175 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/clipped_swiglu/op_kernel/arch35/clipped_swiglu_kernel.h#L175)
- [ChunkGatedDeltaRule A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/chunk_gated_delta_rule.md)（`related`）：算子声明的固定版本源码包含对 `FetchEventID(...)` 的直接调用（第 120 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/chunk_gated_delta_rule/op_kernel/chunk_gated_delta_rule.h#L120)
- [UpsampleBilinear2dAA A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bilinear_2d_aa.md)（`related`）：算子声明的固定版本源码包含对 `FetchEventID(...)` 的直接调用（第 406 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bilinear2d_aa/op_kernel/upsample_bilinear2d_aa.h#L406)
- [CircularPad2d A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/circular_pad_2d.md)（`related`）：算子声明的固定版本源码包含对 `FetchEventID(...)` 的直接调用（第 103 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/circular_pad/op_kernel/circular_pad_common.h#L103)
- [GeGluBackward A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/ge_glu_backward.md)（`related`）：算子声明的固定版本源码包含对 `FetchEventID(...)` 的直接调用（第 424 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/ge_glu_grad_v2/op_kernel/ge_glu_grad_v2_erf_base.h#L424)
- [FlashAttentionScore 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attention_score_950.md)（`related`）：算子声明的固定版本源码包含对 `FetchEventID(...)` 的直接调用（第 1420 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/common/op_kernel/arch35/flash_attention_noquant_block_vec_base.h#L1420)
- [UpsampleBilinear2dAABackward A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bilinear_2d_aa_backward.md)（`related`）：算子声明的固定版本源码包含对 `FetchEventID(...)` 的直接调用（第 499 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bilinear2d_aa_backward/op_kernel/upsample_bilinear2d_aa_backward.h#L499)
- [CircularPad2dBackward A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/circular_pad_2d_backward.md)（`related`）：算子声明的固定版本源码包含对 `FetchEventID(...)` 的直接调用（第 103 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/circular_pad/op_kernel/circular_pad_common.h#L103)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
