---
type: API
title: FetchEventID
description: 根据HardEvent获取相应可用的TEventID，此接口不会申请TEventID，仅提供可用的TEventID。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/FetchEventID.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# FetchEventID

头文件路径为："basic_api/kernel_tpipe.h"。

根据HardEvent（硬件类型的同步事件）获取相应可用的TEventID，此接口不会申请TEventID，仅提供可用的TEventID。

约束：相比于AllocEventID，FetchEventID适用于临时使用ID的场景，获取ID后，不会对ID进行占用。在一些复杂的使用场景下，需要开发者自行保证使用正确。比如相同流水连续调用SetFlag/WaitFlag，如果两次传入的ID都是使用FetchEventID获取的，因为两者ID相同会出现程序卡死等未定义行为，这时推荐用户使用AllocEventID。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [GetTPipePtr 错加 AscendC 命名空间导致编译失败](../../../../../runbooks/compilation/gettpipeptr_is_global_function.md)（`exemplifies`）：“未改 `AscendC::HardEvent`、`FetchEventID` 或同步事件种类，因为报错只指向函数名的命名空间查找；”说明修复后事件调用合同保持不变；“根据HardEvent（硬件类型的同步事件）获取相应可用的TEventID，此接口不会申请TEventID，仅提供可用的TEventID。”定义该成员调用的语义。
- [探针末尾 MTE2_S/MTE3_S 同步不可由 stream sync 替代](../../../../../runbooks/compilation/mte2_s_mte3_s_stream_sync.md)（`exemplifies`）：“- API 路径：`PipeBarrier<PIPE_MTE2｜PIPE_MTE3>`；`GetTPipePtr()->FetchEventID(HardEvent::MTE2_S｜MTE3_S)`；`SetFlag`/`WaitFlag`；Host 侧 `aclrtSynchronizeStream`。”与“根据HardEvent（硬件类型的同步事件）获取相应可用的TEventID，此接口不会申请TEventID，仅提供可用的TEventID。”提供双方正文证据。排障卡在 MTE2_S/MTE3_S 同步序列中实际调用 FetchEventID，API 卡说明它按 HardEvent 返回但不占用 TEventID，支撑该事件配对的资源判断。
- [AllocEventID](alloc_event_id.md)（`related`）：“相比于AllocEventID，FetchEventID适用于临时使用ID的场景，获取ID后，不会对ID进行占用。”给出不占用路线；“用于申请HardEvent（硬件类型同步事件）的TEventID，必须与ReleaseEventID搭配使用，调用该接口后，会占用申请的TEventID，直至调用ReleaseEventID释放。”给出复杂同步需要独占 ID 时的替代生命周期。
- [DequantBias A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/quant/dequant_bias.md)（`related`）：“event_t eventMTE2V = static_cast<event_t>(GetTPipePtr()->FetchEventID(HardEvent::MTE2_V));”给出 DequantBias 的 MTE2→V 临时事件取得方式；“此接口不会申请TEventID，仅提供可用的TEventID。”提示该调用不占用事件 ID，连续复用时需由实现保证安全。
- [ReleaseEventID](release_event_id.md)（`related`）：“相比于AllocEventID，FetchEventID适用于临时使用ID的场景，获取ID后，不会对ID进行占用。”说明 Fetch 路线没有释放生命周期；“AllocEventID、ReleaseEventID需成对出现，ReleaseEventID传入的TEventID需由对应的AllocEventID申请而来。”界定改用独占 ID 后必须履行的释放合同。
- [SetFlag/WaitFlag](../../sync_control/intra_core_sync/set_flag_wait_flag_isasi.md)（`related`）：- 在采用TPipe-TQue框架编程范式时，eventID需要通过AllocEventID或者FetchEventID来获取。；根据HardEvent（硬件类型的同步事件）获取相应可用的TEventID，此接口不会申请TEventID，仅提供可用的TEventID。。同步卡列出 FetchEventID 获取 eventID，目标卡说明它只返回可用 ID 而不占用申请槽位。
<!-- cannbot:related:end -->
